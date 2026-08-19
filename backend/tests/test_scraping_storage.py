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


class ScrapingStorageTestCase(unittest.TestCase):
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

    def test_save_records_inserts_updates_skips_and_soft_disables(self):
        first = self._record()
        second = self._record("anapec_emploi:2", "hash-2")

        self.assertEqual(
            storage.save_records([first, second]),
            {
                "records": 2,
                "new_records": 2,
                "updated_records": 0,
                "unchanged_records": 0,
                "duplicate_records": 0,
                "expired_records": 0,
                "errors": 0,
            },
        )
        self.assertEqual(storage.save_records([first, second])["unchanged_records"], 2)

        changed = self._record(content_hash="hash-1b", description="Comptable senior - AGADIR")
        stats = storage.save_records([changed], deactivate_missing=True)

        self.assertEqual(stats["updated_records"], 1)
        self.assertEqual(stats["expired_records"], 1)

        db = self.SessionLocal()
        try:
            rows = db.query(Aides).order_by(Aides.source_record_id).all()
            self.assertEqual(len(rows), 2)
            self.assertTrue(rows[0].est_active)
            self.assertEqual(rows[0].description, "Comptable senior - AGADIR")
            self.assertFalse(rows[1].est_active)
        finally:
            db.close()

    def test_duplicate_source_record_ids_are_counted(self):
        first = self._record()
        duplicate = self._record(description="Dernière version", content_hash="hash-1b")

        stats = storage.save_records([first, duplicate])

        self.assertEqual(stats["records"], 2)
        self.assertEqual(stats["duplicate_records"], 1)
        self.assertEqual(stats["new_records"], 1)


if __name__ == "__main__":
    unittest.main()
