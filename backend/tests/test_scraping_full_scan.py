import os
import sys
import unittest
from datetime import date
from pathlib import Path

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret")
os.environ.setdefault("ALGORITHM", "HS256")

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.database import Base
from app.models.aides import Aides
from app.scraping import storage
from app.scraping.sources.anapec.emploi import _compute_full_scan


class FullScanComputationTestCase(unittest.TestCase):
    """Vérifie la règle de sécurité du full_scan."""

    def test_full_scan_true_when_all_pages_fetched_successfully(self):
        """Cas 1 — Scan complet réussi : toutes les pages récupérées."""
        self.assertTrue(
            _compute_full_scan(
                page_limit=100,
                total_pages_available=100,
                pages_fetched=100,
                pages_failed=0,
            )
        )

    def test_full_scan_false_when_one_page_failed(self):
        """Cas 2 — Scan complet avec une page en échec."""
        self.assertFalse(
            _compute_full_scan(
                page_limit=100,
                total_pages_available=100,
                pages_fetched=99,
                pages_failed=1,
            )
        )

    def test_full_scan_false_in_incremental_mode(self):
        """Cas 3 — Mode incrémental normal (20 pages sur 725)."""
        self.assertFalse(
            _compute_full_scan(
                page_limit=20,
                total_pages_available=725,
                pages_fetched=20,
                pages_failed=0,
            )
        )

    def test_full_scan_false_when_fetched_less_than_limit(self):
        """full_scan reste False si moins de pages que prévu ont été récupérées."""
        self.assertFalse(
            _compute_full_scan(
                page_limit=100,
                total_pages_available=100,
                pages_fetched=50,
                pages_failed=0,
            )
        )

    def test_full_scan_false_when_parsing_failed(self):
        """Une page échouée au parsing (snapshot manquant) empêche full_scan."""
        self.assertFalse(
            _compute_full_scan(
                page_limit=100,
                total_pages_available=100,
                pages_fetched=99,
                pages_failed=1,
            )
        )


class SoftDisableSafetyTestCase(unittest.TestCase):
    """Vérifie qu'aucune offre n'est désactivée lors d'une collecte partielle."""

    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(bind=self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)
        self.original_session_local = storage.SessionLocal
        storage.SessionLocal = self.SessionLocal

    def tearDown(self):
        storage.SessionLocal = self.original_session_local
        self.engine.dispose()

    def _record(self, key="anapec_emploi:1", content_hash="hash-1", description="Comptable - AGADIR"):
        return {
            "source_nom": "ANAPEC",
            "source_url": "https://anapec.ma",
            "source_type": "Organisme public",
            "source_fiable": True,
            "categorie_nom": "Offres d'emploi",
            "categorie_description": "Offres ANAPEC",
            "titre": "Comptable",
            "description": description,
            "date_limite": None,
            "type_aide": "Offre d'emploi",
            "montant": None,
            "age_min": None,
            "age_max": None,
            "region_cible": "AGADIR",
            "niveau_etude_requis": None,
            "statut_socio_pro_requis": None,
            "handicap_requis": False,
            "url_officielle": "https://anapec.ma/chercheurs/offres",
            "image_url": None,
            "source_record_id": key,
            "reference_offre": key.rsplit(":", 1)[-1],
            "entreprise_nom": None,
            "date_publication": date(2026, 8, 19),
            "lieu_travail": "AGADIR",
            "content_hash": content_hash,
        }

    def test_existing_offer_not_deactivated_on_partial_collection(self):
        """Cas 4 — Offre existante absente d'une collecte partielle.

        Une offre existe en DB mais n'est pas présente dans les résultats
        parce qu'une partie du site n'a pas été collectée (deactivate_missing=False).
        Elle doit rester active.
        """
        existing = self._record()
        storage.save_records([existing])

        # Collecte partielle : une autre offre est récupérée, mais pas l'offre
        # existante. deactivate_missing=False car full_scan=False (page en échec).
        other = self._record("anapec_emploi:2", "hash-2", description="Ingénieur - CASABLANCA")
        stats = storage.save_records([other], deactivate_missing=False)

        self.assertEqual(stats["expired_records"], 0)

        db = self.SessionLocal()
        try:
            row = db.query(Aides).filter(Aides.source_record_id == "anapec_emploi:1").first()
            self.assertIsNotNone(row)
            self.assertTrue(row.est_active)
        finally:
            db.close()

    def test_existing_offer_deactivated_only_on_full_scan(self):
        """Le soft-disable n'a lieu que si deactivate_missing=True (full_scan garanti)."""
        first = self._record()
        second = self._record("anapec_emploi:2", "hash-2")
        storage.save_records([first, second])

        # Scan complet : seule l'offre 1 est présente, l'offre 2 est réellement absente.
        stats = storage.save_records([first], deactivate_missing=True)

        self.assertEqual(stats["expired_records"], 1)

        db = self.SessionLocal()
        try:
            rows = db.query(Aides).order_by(Aides.source_record_id).all()
            self.assertTrue(rows[0].est_active)
            self.assertFalse(rows[1].est_active)
        finally:
            db.close()


if __name__ == "__main__":
    unittest.main()