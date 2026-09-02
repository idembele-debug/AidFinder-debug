# -*- coding: utf-8 -*-
"""Tests backend de la modification de profil (PATCH /users/me).

Couvre les exigences du chantier :
1. Rejet explicite des champs inconnus (extra="forbid" → 422).
2. Rejet d'un payload sans aucun champ modifiable (400).
3. Modification d'un seul champ persistée en base.
4. Modification de plusieurs champs persistée en base.
5. La valeur persistée est bien celle envoyée (SQLAlchemy → SQLite/PostgreSQL).
"""

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

from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.database import Base
from app.models.utilisateurs import Utilisateur
from app.schemas.utilisateur import UserProfileUpdate
from app.services.user_service import update_user_profile


def _make_user(session, **overrides):
    fields = {
        "nom": "Test User",
        "email": "profile@example.com",
        "mot_de_passe_hash": "hash",
        "role": "utilisateur",
        "statut_compte": "actif",
        "date_naissance": date(1995, 5, 5),
        "ville": "Casablanca",
        "region": "Casablanca-Settat",
        "niveau_etude": "Bac+2",
        "statut_socio_pro": "Employé",
        "situation_handicap": False,
    }
    fields.update(overrides)
    user = Utilisateur(**fields)
    session.add(user)
    session.commit()
    return user


class UserProfileUpdateTestCase(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine(
            "sqlite:///:memory:", connect_args={"check_same_thread": False}
        )
        Base.metadata.create_all(bind=self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)
        self.db = self.SessionLocal()
        self.user = _make_user(self.db)

    def tearDown(self):
        self.db.close()
        self.engine.dispose()

    def _fresh_user(self):
        return (
            self.db.query(Utilisateur)
            .filter(Utilisateur.user_id == self.user.user_id)
            .first()
        )

    # -- 1. Champ inconnu → ValidationError (équivalent HTTP 422) -------
    def test_unknown_field_rejected(self):
        with self.assertRaises(ValidationError):
            UserProfileUpdate(**{"champ_inconnu": "x"})
        with self.assertRaises(ValidationError):
            UserProfileUpdate(**{"nom": "Nouveau", "fake_field": 42})

    # -- 2. Payload vide → HTTP 400 -------------------------------------
    def test_empty_payload_rejected(self):
        with self.assertRaises(HTTPException) as ctx:
            update_user_profile(self.db, self.user, UserProfileUpdate())
        self.assertEqual(ctx.exception.status_code, 400)

    # -- 3. Modification d'un seul champ persistée ----------------------
    def test_update_single_field(self):
        updated = update_user_profile(
            self.db, self.user, UserProfileUpdate(nom="Nouveau Nom")
        )
        self.assertEqual(updated.nom, "Nouveau Nom")
        fresh = self._fresh_user()
        self.assertEqual(fresh.nom, "Nouveau Nom")
        # Les autres champs ne bougent pas
        self.assertEqual(fresh.region, "Casablanca-Settat")
        self.assertEqual(fresh.niveau_etude, "Bac+2")

    # -- 4. Modification de plusieurs champs persistée ------------------
    def test_update_multiple_fields(self):
        update_user_profile(
            self.db,
            self.user,
            UserProfileUpdate(
                region="Rabat-Salé-Kénitra",
                niveau_etude="Licence",
            ),
        )
        fresh = self._fresh_user()
        self.assertEqual(fresh.region, "Rabat-Salé-Kénitra")
        self.assertEqual(fresh.niveau_etude, "Licence")

    # -- 5. La valeur persistée == valeur envoyée -----------------------
    def test_persisted_value_equals_sent(self):
        update_user_profile(
            self.db, self.user, UserProfileUpdate(situation_handicap=True)
        )
        self.assertTrue(self._fresh_user().situation_handicap)

        update_user_profile(
            self.db,
            self.user,
            UserProfileUpdate(date_naissance=date(2004, 9, 26)),
        )
        self.assertEqual(self._fresh_user().date_naissance, date(2004, 9, 26))

    # -- 6. Le champ ville n'est pas cassé par le formulaire -------------
    def test_ville_kept_when_other_fields_updated(self):
        update_user_profile(self.db, self.user, UserProfileUpdate(region="Fès-Meknès"))
        self.assertEqual(self._fresh_user().ville, "Casablanca")


if __name__ == "__main__":
    unittest.main()