# -*- coding: utf-8 -*-
"""Test de non-régression : POST /dashboard/chat avec recommandations présentes.

Reproduit EXACTEMENT le bug corrigé :
- « Je cherche une offre d'emploi » avec un profil suffisant et des offres en
  base → `POST /dashboard/chat` (response_model=ChatMessageResponse) exige que
  chaque élément de `aides_recommandees` valide `DashboardAidResponse`, dont le
  champ requis `id: int`.
- `recommendation_engine._serialize_aids` ne renvoyait que `aide_id` (pas `id`)
  → FastAPI levait `ResponseValidationError` → HTTP 500.

Couvre :
1. Le flux HTTP complet (TestClient) répond 200 et non 500, les recommandations
   portent `id` ET `aide_id` (valeurs identiques).
2. La réponse est valide vis-à-vis de `ChatMessageResponse` / `DashboardAidResponse`.
3. `url_officielle` / `lien_officiel` sont préservés.
4. Le payload envoyé à Dify (`inputs["recommendations"]`) reste inchangé
   (pas de clé `id`) : le comportement/prompt Dify ne bouge pas.
5. L'événement SSE `done` du streaming porte aussi `id`.
6. `conversation_id` Dify persisté et réutilisé entre deux messages (Memory).
"""

import asyncio
import os
import sys
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret")
os.environ.setdefault("ALGORITHM", "HS256")

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.securite import get_current_user
from app.database.session import get_db
from app.database.database import Base
from app.models.aides import Aides
from app.models.utilisateurs import Utilisateur
from app.routes.dashboard import router as dashboard_router
from app.schemas.chat import ChatMessageResponse
from app.schemas.dashboard import DashboardAidResponse
from app.services.chat_service import chat_service

OFFRE_URL = "https://anapec.ma/chercheurs/offres"


def _make_user(session, **overrides):
    fields = {
        "nom": "Profil Schema",
        "email": "schema@example.com",
        "mot_de_passe_hash": "x",
        "role": "utilisateur",
        "statut_compte": "actif",
        "date_naissance": date(1995, 5, 5),  # ~30 ans
        "ville": "Casablanca",
        "region": "Casablanca-Settat",
        "niveau_etude": "Licence",
        "statut_socio_pro": "Demandeur d'emploi",
        "situation_handicap": False,
    }
    fields.update(overrides)
    user = Utilisateur(**fields)
    session.add(user)
    session.commit()
    return user


def _make_aide(session, titre, region="Casablanca"):
    aide = Aides(
        source_id=None,
        categorie_id=None,
        titre=titre,
        description=f"{titre} - {region}",
        type_aide="Offre d'emploi",
        region_cible=region,
        niveau_etude_requis="Licence",
        statut_socio_pro_requis="Demandeur d'emploi",
        age_min=None,
        age_max=None,
        handicap_requis=False,
        content_hash="hash-" + titre,
        est_active=True,
        url_officielle=OFFRE_URL,
    )
    session.add(aide)
    session.commit()
    return aide


def _dify_ok_response():
    return {
        "success": True,
        "answer": "Voici des offres pour vous.",
        "conversation_id": "cid-memory-1",
        "raw": {},
    }


class ChatHttpRegressionTestCase(unittest.TestCase):
    """Reproduction exacte via le routeur HTTP : 500 → 200."""

    def setUp(self):
        # TestClient exécute les routes dans un thread dédié : ce pool partagé
        # (StaticPool) garantit que la SAME connexion SQLite :memory: sert le
        # thread du serveur de test et le thread du test (sinon chaque thread
        # verrait une base vide → « no such table »).
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(bind=self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine, class_=Session, expire_on_commit=False)
        self.db = self.SessionLocal()
        self.user = _make_user(self.db)
        _make_aide(self.db, "Developpeur - CASABLANCA")

        self.app = FastAPI()
        self.app.include_router(dashboard_router)

        def override_get_db():
            yield self.db

        def override_get_current_user():
            return self.user

        self.app.dependency_overrides[get_db] = override_get_db
        self.app.dependency_overrides[get_current_user] = override_get_current_user

    def tearDown(self):
        self.app.dependency_overrides.clear()
        self.db.close()
        self.engine.dispose()

    def test_post_dashboard_chat_returns_200_with_valid_recommendations(self):
        from app.services import response_generator as rg

        with patch.object(rg, "dify_client") as mock_dify:
            mock_dify.send_message.return_value = _dify_ok_response()

            client = TestClient(self.app)
            resp = client.post(
                "/dashboard/chat",
                json={"message": "Je cherche une offre d'emploi"},
                headers={"Authorization": "Bearer test"},
            )

        # Le bug produisait un HTTP 500 (ResponseValidationError).
        self.assertEqual(resp.status_code, 200, resp.text)

        data = resp.json()
        recos = data["aides_recommandees"]
        self.assertTrue(recos, "Des recommandations doivent être présentes")

        for reco in recos:
            self.assertIn("id", reco, "la clé `id` exigée par le schéma doit exister")
            self.assertIn("aide_id", reco, "la clé `aide_id` (frontend) doit rester")
            self.assertEqual(reco["id"], reco["aide_id"])
            self.assertEqual(reco["url_officielle"], OFFRE_URL)


class ChatSchemaValidationTestCase(unittest.TestCase):
    """Le schéma Pydantic valide strictement la réponse enrichie."""

    def setUp(self):
        self.engine = create_engine(
            "sqlite:///:memory:", connect_args={"check_same_thread": False}
        )
        Base.metadata.create_all(bind=self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)
        self.db = self.SessionLocal()
        self.user = _make_user(self.db)
        _make_aide(self.db, "Developpeur - CASABLANCA")

    def tearDown(self):
        self.db.close()
        self.engine.dispose()

    def test_response_respects_chatmessage_schema(self):
        from app.services import response_generator as rg

        with patch.object(rg, "dify_client") as mock_dify:
            mock_dify.send_message.return_value = _dify_ok_response()
            resp = chat_service.handle_message(
                self.db, self.user, "Je cherche une offre d'emploi"
            )

        recos = resp["aides_recommandees"]
        self.assertTrue(recos)

        # Validation Pydantic EXACTE (ce que FastAPI fait avant de répondre).
        validated = ChatMessageResponse.model_validate(resp)
        self.assertEqual(len(validated.aides_recommandees), len(recos))

        for reco in recos:
            parsed = DashboardAidResponse.model_validate(reco)
            self.assertEqual(parsed.id, parsed.aide_id)
            self.assertTrue(parsed.url_officielle)
            self.assertEqual(parsed.url_officielle, reco["lien_officiel"])

    def test_dify_payload_recommendations_unchanged(self):
        """La correction ne doit PAS ajouter `id` au payload transmis à Dify."""
        from app.services import response_generator as rg

        with patch.object(rg, "dify_client") as mock_dify:
            mock_dify.send_message.return_value = _dify_ok_response()
            chat_service.handle_message(
                self.db, self.user, "Je cherche une offre d'emploi"
            )
            inputs = mock_dify.send_message.call_args[1].get("inputs", {})
            recos_dify = inputs.get("recommendations") or []

        self.assertTrue(recos_dify)
        self.assertIn("aide_id", recos_dify[0])
        self.assertNotIn(
            "id", recos_dify[0],
            "le payload Dify doit rester strictement inchangé",
        )

    def test_streaming_done_event_contains_id(self):
        from app.services import response_generator as rg

        def fake_stream(message, conversation_id=None, inputs=None):
            yield {"success": True, "answer": "Voici", "conversation_id": "cs1", "raw": {}}
            yield {"success": True, "answer": " des offres", "conversation_id": "cs1", "raw": {}}

        async def run():
            done = None
            async for ev in chat_service.handle_message_stream(
                self.db, self.user, "Je cherche une offre d'emploi"
            ):
                if ev.get("type") == "done":
                    done = ev["data"]
            return done

        with patch.object(rg, "dify_client") as mock_dify:
            mock_dify.send_message_stream.side_effect = fake_stream
            done = asyncio.run(run())

        recos = done["aides_recommandees"]
        self.assertTrue(recos)
        for reco in recos:
            self.assertEqual(reco["id"], reco["aide_id"])
            self.assertEqual(reco["url_officielle"], reco["lien_officiel"])
            self.assertEqual(reco["url_officielle"], OFFRE_URL)

    def test_conversation_id_memory_persisted_and_reused(self):
        from app.services import response_generator as rg

        with patch.object(rg, "dify_client") as mock_dify:
            mock_dify.send_message.return_value = _dify_ok_response()
            r1 = chat_service.handle_message(
                self.db, self.user, "Je cherche une offre d'emploi"
            )
            hid = r1["historique_id"]
            chat_service.handle_message(
                self.db, self.user, "encore", historique_id=hid
            )
            calls = mock_dify.send_message.call_args_list

        # 2e appel → conversation_id Dify reçu au 1er tour.
        self.assertEqual(len(calls), 2)
        self.assertEqual(calls[1][1].get("conversation_id"), "cid-memory-1")


if __name__ == "__main__":
    unittest.main()