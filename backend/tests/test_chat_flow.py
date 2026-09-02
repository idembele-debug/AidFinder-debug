# -*- coding: utf-8 -*-
"""Tests ciblés du flux chatbot après fusion du double appel Dify.

Couvre :
1. Un seul appel Dify quand le profil est complet + recommandations.
2. Aucune recommandation quand le profil est incomplet.
3. Persistance et réutilisation du conversation_id Dify.
4. Fallback ConversationFallback quand Dify échoue.
5. Streaming SSE : chunks puis done, un seul appel.
"""

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

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.database import Base
from app.models.utilisateurs import Utilisateur
from app.models.aides import Aides
from app.models.categorie_aide import CategorieAide
from app.services.chat_service import chat_service


def _make_user(session, **overrides):
    fields = {
        "nom": "Test",
        "email": "test@example.com",
        "mot_de_passe_hash": "x",
        "role": "utilisateur",
        "statut_compte": "actif",
        "ville": "Casablanca",
        "region": "Casablanca-Settat",
        "niveau_etude": "ingenieur",
        "statut_socio_pro": "employe",
        "date_naissance": date(1995, 5, 5),  # ~30 ans
        "situation_handicap": False,
    }
    fields.update(overrides)
    user = Utilisateur(**fields)
    session.add(user)
    session.commit()
    return user


def _make_aide(session, titre="Developpeur - CASABLANCA"):
    return Aides(
        source_id=None,
        categorie_id=None,
        titre=titre,
        description=titre,
        type_aide="Offre d'emploi",
        region_cible="Casablanca",
        niveau_etude_requis="ingenieur",
        statut_socio_pro_requis="employe",
        age_min=None,
        age_max=None,
        handicap_requis=False,
        content_hash="hash-" + titre,
        est_active=True,
        url_officielle="https://anapec.ma/offre",
    )

class ChatFlowTestCase(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine(
            "sqlite:///:memory:", connect_args={"check_same_thread": False}
        )
        Base.metadata.create_all(bind=self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)
        self.db = self.SessionLocal()
        self.user = _make_user(self.db)

        cat = CategorieAide(nom="Offres d'emploi", description="ca")
        self.db.add(cat)
        self.db.commit()

        aide = _make_aide(self.db)
        aide.categorie_id = cat.categorie_id
        self.db.add(aide)
        self.db.commit()
        self.aide = aide

    def tearDown(self):
        self.db.close()
        self.engine.dispose()

    # -- Test 1 : un seul appel Dify (profil complet + reco) ---
    def test_single_dify_call_with_recommendations(self):
        from app.services import response_generator as rg

        with patch.object(rg, "dify_client") as mock_dify:
            mock_dify.send_message.return_value = {
                "success": True,
                "answer": "Voici des offres pour vous.",
                "conversation_id": "c1",
                "raw": {},
            }
            resp = chat_service.handle_message(
                self.db, self.user, "Je cherche un emploi à Casablanca"
            )
            self.assertEqual(mock_dify.send_message.call_count, 1)
            inputs = mock_dify.send_message.call_args[1].get("inputs", {})
            self.assertIn("recommendations", inputs)
            self.assertTrue(len(inputs["recommendations"]) > 0)
            self.assertTrue(resp["aides_recommandees"])

    # -- Test 2 : profil incomplet -> aucune reco, chatbot fonctionne ---
    def test_incomplete_profile_no_recommendations(self):
        from app.services import response_generator as rg

        user_incomplete = _make_user(
            self.db, email="incomplete@example.com", ville="", region="",
            niveau_etude="", statut_socio_pro="", date_naissance=None,
            situation_handicap=False,
        )
        with patch.object(rg, "dify_client") as mock_dify:
            mock_dify.send_message.return_value = {
                "success": True, "answer": "Pouvez-vous me donner votre ville ?",
                "conversation_id": "c2", "raw": {},
            }
            resp = chat_service.handle_message(self.db, user_incomplete, "bonjour")
            self.assertEqual(mock_dify.send_message.call_count, 1)
            self.assertFalse(resp["aides_recommandees"])
            self.assertTrue(resp["bot_message"]["contenu"])


    # -- Test 3 : conversation_id persisté et réutilisé ------------------
    def test_conversation_id_persisted_and_reused(self):
        from app.services import response_generator as rg

        with patch.object(rg, "dify_client") as mock_dify:
            def fake_send(message, conversation_id=None, inputs=None):
                return {
                    "success": True,
                    "answer": "ok",
                    "conversation_id": "cid-123",
                    "raw": {},
                }
            mock_dify.send_message.side_effect = fake_send

            r1 = chat_service.handle_message(
                self.db, self.user, "Je cherche un emploi"
            )
            hid = r1["historique_id"]
            chat_service.handle_message(
                self.db, self.user, "encore", historique_id=hid
            )

            cid_calls = [
                c[1].get("conversation_id")
                for c in mock_dify.send_message.call_args_list
            ]
            # 2e appel (index 1) doit porter l'id reçu au 1er
            self.assertEqual(cid_calls[1], "cid-123")

    # -- Test 4 : fallback quand Dify échoue -----------------------------
    def test_fallback_when_dify_fails(self):
        from app.services import response_generator as rg

        with patch.object(rg, "dify_client") as mock_dify:
            mock_dify.send_message.return_value = {
                "success": False, "error": "boom", "raw": {}
            }
            resp = chat_service.handle_message(
                self.db, self.user, "Je cherche un emploi"
            )
            self.assertTrue(resp["bot_message"]["contenu"])
            self.assertIsInstance(resp["aides_recommandees"], list)

    # -- Test 5 : streaming -> chunks + done, un seul appel --------------
    def test_streaming_single_call_and_format(self):
        import asyncio
        from app.services import response_generator as rg

        with patch.object(rg, "dify_client") as mock_dify:
            def fake_stream(message, conversation_id=None, inputs=None):
                yield {"success": True, "answer": "Bon", "conversation_id": "cs1", "raw": {}}
                yield {"success": True, "answer": "jour", "conversation_id": "cs1", "raw": {}}

            mock_dify.send_message_stream.side_effect = fake_stream

            async def run():
                events = []
                results = []
                async for ev in chat_service.handle_message_stream(
                    self.db, self.user, "Je cherche un emploi à Casablanca"
                ):
                    events.append(ev)
                    if ev.get("type") == "done":
                        results.append(ev["data"])
                return events, results, mock_dify.send_message_stream.call_count

            events, results, call_count = asyncio.run(run())
            self.assertEqual(call_count, 1)
            types = [e.get("type") for e in events]
            self.assertIn("chunk", types)
            self.assertIn("done", types)

            # Les recommandations de l'événement SSE "done" doivent porter la
            # clé canonique attendue par le frontend : `url_officielle`.
            self.assertTrue(results[0]["aides_recommandees"])
            reco = results[0]["aides_recommandees"][0]
            self.assertEqual(reco["url_officielle"], reco["lien_officiel"])
            self.assertEqual(reco["url_officielle"], "https://anapec.ma/offre")


if __name__ == "__main__":
    unittest.main()

