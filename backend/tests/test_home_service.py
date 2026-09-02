# -*- coding: utf-8 -*-
"""Tests des compteurs de la page d'accueil et de l'admin.

Exigence du chantier : le compteur « aides » affiché par la plateforme doit
correspondre aux données réellement présentes et exploitables — c'est-à-dire
aux offres ACTIVES uniquement (les offres scrapées puis désactivées ne doivent
pas gonfler le chiffre).
"""

import os
import sys
import unittest
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
from app.services.home_service import get_home_stats, get_latest_aids


def _make_aide(session, titre, actif=True):
    aide = Aides(
        titre=titre,
        description=titre,
        type_aide="Offre d'emploi",
        region_cible="Casablanca",
        content_hash="hash-" + titre,
        url_officielle="https://anapec.ma/chercheurs/offres",
        est_active=actif,
    )
    session.add(aide)
    return aide


class HomeStatsTestCase(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine(
            "sqlite:///:memory:", connect_args={"check_same_thread": False}
        )
        Base.metadata.create_all(bind=self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)
        self.db = self.SessionLocal()
        _make_aide(self.db, "Offre active 1", actif=True)
        _make_aide(self.db, "Offre active 2", actif=True)
        _make_aide(self.db, "Offre désactivée", actif=False)
        self.db.commit()

    def tearDown(self):
        self.db.close()
        self.engine.dispose()

    def test_home_stats_counts_only_active(self):
        stats = get_home_stats(self.db)
        self.assertEqual(stats["total_aides"], 2)

    def test_latest_aids_only_active(self):
        aides = get_latest_aids(self.db, limit=10)
        self.assertEqual(len(aides), 2)
        self.assertTrue(all(a["titre"] != "Offre désactivée" for a in aides))


if __name__ == "__main__":
    unittest.main()