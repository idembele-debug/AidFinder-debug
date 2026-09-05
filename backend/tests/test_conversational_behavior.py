# -*- coding: utf-8 -*-
"""Tests du comportement conversationnel naturel et progressif d'AidFinder.

Reproduit les exigences de la mission « conversation naturelle » :
- jamais plus d'une question par message, uniquement si réellement nécessaire ;
- aucune question sur une information déjà connue (profil ou conversation) ;
- réponses courtes et chaleureuses pour les salutations ;
- pas de listes à puces excessives dans les échanges conversationnels ;
- aucun organisme français (France Travail, APEC, CROUS…) en contexte marocain ;
- aucun conseil de candidature (CV, LinkedIn, GitHub…) non demandé ;
- recherche déclenchée dès que les informations minimales sont disponibles ;
- comportement du recommendation_engine conservé.
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

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.database import Base
from app.models.aides import Aides
from app.models.utilisateurs import Utilisateur
from app.services.chat_service import chat_service
from app.services.recommendation_engine import recommendation_engine


FORBIDDEN_FR_PLATFORMS = (
    "france travail",
    "pôle emploi",
    "pole emploi",
    "apec",
    "mission locale",
    "crous",
    "indeed",
    "hellowork",
    "hello work",
    "linkedin jobs",
    "caf ",
    "titre de séjour",
)
FORBIDDEN_JOB_ADVICE = ("cv", "linkedin", "github", "portfolio", "lettre de motivation")


def _bullet_lines(text: str) -> int:
    """Compte les lignes de liste (« - », « • », « 1. »…) dans un texte."""
    count = 0
    for raw in text.split("\n"):
        line = raw.strip()
        if not line:
            continue
        if line.startswith(("•", "-", "*")):
            count += 1
        elif len(line) > 1 and line[0].isdigit() and line[1] == ".":
            count += 1
    return count


def _make_user(session, **overrides):
    fields = {
        "nom": "Profil Complet",
        "email": "complet@example.com",
        "mot_de_passe_hash": "x",
        "role": "utilisateur",
        "statut_compte": "actif",
        "date_naissance": date(2004, 9, 26),  # ~21 ans
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


def _make_aide(session, titre, region, niveau=None):
    aide = Aides(
        source_id=None,
        categorie_id=None,
        titre=titre,
        description=f"{titre} - {region}",
        type_aide="Offre d'emploi",
        region_cible=region,
        niveau_etude_requis=niveau,
        statut_socio_pro_requis=None,
        age_min=None,
        age_max=None,
        handicap_requis=False,
        content_hash="hash-" + titre,
        source_record_id="anapec_emploi:" + titre,
        entreprise_nom="Entreprise Maroc",
        lieu_travail=region,
        est_active=True,
        url_officielle="https://anapec.ma/chercheurs/offres",
    )
    session.add(aide)
    return aide


class ConversationalBehaviorTestCase(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine(
            "sqlite:///:memory:", connect_args={"check_same_thread": False}
        )
        Base.metadata.create_all(bind=self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)
        self.db = self.SessionLocal()
        self.user = _make_user(self.db)

        # Base d'offres marocaines variées.
        _make_aide(self.db, "Développeur Full-Stack", "Casablanca", niveau="Licence")
        _make_aide(self.db, "Comptable Confirmé", "Casablanca", niveau="Licence")
        self.db.commit()

    def tearDown(self):
        self.db.close()
        self.engine.dispose()
# -- Helpers ----------------------------------------------------------

    def _fallback(self, message, user=None, historique_id=None):
        """Fait parler le chatbot via le fallback déterministe (Dify en échec)."""
        target = user or self.user
        with patch("app.services.response_generator.dify_client") as mock_dify:
            mock_dify.send_message.return_value = {
                "success": False, "error": "boom", "raw": {},
            }
            return chat_service.handle_message(
                self.db, target, message, historique_id=historique_id
            )

    def _dify(self, message, user=None, historique_id=None):
        """Appel via Dify simulé en succès, retourne (réponse, inputs)."""
        target = user or self.user
        with patch("app.services.response_generator.dify_client") as mock_dify:
            mock_dify.send_message.return_value = {
                "success": True, "answer": "Réponse test", "conversation_id": "cid", "raw": {},
            }
            resp = chat_service.handle_message(
                self.db, target, message, historique_id=historique_id
            )
            inputs = mock_dify.send_message.call_args[1].get("inputs", {})
            return resp, inputs

    def _assert_no_french(self, contenu):
        nettoye = contenu.lower().replace("anapec", "aidfinder")
        for plateforme in FORBIDDEN_FR_PLATFORMS:
            self.assertNotIn(plateforme, nettoye, f"Plateforme FR dans : {contenu}")

    def _assert_no_job_advice(self, contenu):
        bas = contenu.lower()
        for mot in FORBIDDEN_JOB_ADVICE:
            self.assertNotIn(mot, bas, f"Conseil de candidature dans : {contenu}")

    # -- Test 1 : Bonjour → court, chaleureux, aucune liste ni questionnaire --
    def test_greeting_is_short_and_warm_without_questionnaire(self):
        resp = self._fallback("Bonjour")
        contenu = resp["bot_message"]["contenu"]
        bas = contenu.lower()

        self.assertIn("aidfinder", bas)
        self.assertLessEqual(len(contenu), 220, "Réponse de salutation trop longue")
        self.assertEqual(_bullet_lines(contenu), 0, "Liste inutile dans une salutation")
        self.assertLessEqual(contenu.count("?"), 1, "Plus d'une question à la salutation")
        self.assertFalse(resp["aides_recommandees"])
        self.assertIsNone(resp["question_actuelle"])
        self._assert_no_french(contenu)
        self._assert_no_job_advice(contenu)

    # -- Test : profil incomplet + Bonjour → pas de question de profil -----
    def test_greeting_with_incomplete_profile_does_not_ask_profile(self):
        user_no_location = _make_user(
            self.db,
            email="noloc2@example.com",
            ville="",
            region="",
            niveau_etude="",
            statut_socio_pro="",
        )
        resp = self._fallback("Bonjour", user=user_no_location)
        contenu = resp["bot_message"]["contenu"].lower()

        self.assertIsNone(resp["question_actuelle"],
                          "Une salutation ne doit pas poser de question de profil")
        self.assertLessEqual(len(contenu), 220)
        self.assertNotIn("ville", contenu)
        self._assert_no_french(contenu)

    # -- Test : localisation manquante → UNE seule question (localisation) --
    def test_job_search_with_missing_location_asks_only_location(self):
        user_no_location = _make_user(
            self.db,
            email="noloc3@example.com",
            ville="",
            region="",
            niveau_etude="Licence",
            statut_socio_pro="Demandeur d'emploi",
        )
        resp = self._fallback("Je cherche une offre d'emploi", user=user_no_location)
        contenu = resp["bot_message"]["contenu"]

        self.assertFalse(resp["aides_recommandees"])
        self.assertEqual(resp["champs_manquants"], ["ville"])
        self.assertIsNotNone(resp["question_actuelle"])
        self.assertIn("ville", resp["question_actuelle"].lower())
        self.assertEqual(contenu.count("?"), 1, "Une seule question demandée")

        question = contenu.lower()
        for mots in ("niveau", "statut ", "handicap", "cv", "linkedin"):
            self.assertNotIn(mots, question, f"Questionnaire dans : {contenu}")
        self._assert_no_french(contenu)

    # -- Test : emploi développeur → offre concrète, pas de guide ----------
    def test_job_search_developer_no_guide_no_cv_no_french(self):
        resp = self._fallback("Je cherche un emploi de développeur")
        contenu = resp["bot_message"]["contenu"]
        bas = contenu.lower()

        self.assertTrue(resp["aides_recommandees"], "Une recherche doit produire des offres")
        self.assertTrue(bas.strip().startswith("voici") or "voici" in bas)
        self.assertIn("consulter", bas)
        self.assertIsNone(resp["question_actuelle"])
        self.assertEqual(contenu.count("?"), 1, "Max une question après les recommandations")
        self._assert_no_french(contenu)
        self._assert_no_job_advice(contenu)

    # -- Test : recherche déclenchée avec les infos minimales --------------
    def test_search_triggered_with_minimal_profile(self):
        user_minimal = _make_user(
            self.db,
            email="mini@example.com",
            ville="",
            niveau_etude="",
            statut_socio_pro="",
        )
        resp = self._fallback("Je cherche un emploi", user=user_minimal)
        self.assertTrue(resp["aides_recommandees"])
        self.assertIsNone(resp["question_actuelle"])

    # -- Test : demande vague → question ouverte, pas de collecte profil ---
    def test_vague_request_opens_conversation_without_collecting(self):
        user_no_location = _make_user(
            self.db,
            email="vague@example.com",
            ville="",
            region="",
            niveau_etude="",
            statut_socio_pro="",
        )
        resp = self._fallback("Je cherche autre chose", user=user_no_location)
        contenu = resp["bot_message"]["contenu"]

        self.assertIsNone(resp["question_actuelle"])
        self.assertEqual(contenu.count("?"), 1)
        self.assertIn("cherches", contenu.lower())
        self.assertNotIn("ville", contenu.lower())
        self.assertEqual(_bullet_lines(contenu), 0)
        self._assert_no_french(contenu)

    # -- Test : progressif — localisation puis recommandations, sans re-questionner --
    def test_progressive_job_search_asks_then_recommends(self):
        user_no_location = _make_user(
            self.db,
            email="prog@example.com",
            ville="",
            region="",
            niveau_etude="Licence",
            statut_socio_pro="Demandeur d'emploi",
        )
        r1 = self._fallback("Je cherche un emploi", user=user_no_location)
        self.assertIsNotNone(r1["question_actuelle"])
        self.assertIn("ville", r1["question_actuelle"].lower())

        # Étape suivante : l'utilisateur répond simplement « Casablanca ».
        r2 = self._fallback(
            "Casablanca", user=user_no_location, historique_id=r1["historique_id"]
        )
        contenu = r2["bot_message"]["contenu"].lower()
        self.assertTrue(r2["aides_recommandees"],
                        "La recherche doit se déclencher une fois la ville connue")
        self.assertIsNone(r2["question_actuelle"])
        self.assertNotIn("quelle ville", contenu, "La ville est déjà connue")
        self._assert_no_french(r2["bot_message"]["contenu"])

    # -- Test : demande très précise → pas de re-demande de la ville -------
    def test_precise_request_casablanca_not_requestioned(self):
        user_no_location = _make_user(
            self.db,
            email="precise@example.com",
            ville="",
            region="",
        )
        resp = self._fallback("Je cherche un emploi à Casablanca", user=user_no_location)
        contenu = resp["bot_message"]["contenu"].lower()

        self.assertTrue(resp["aides_recommandees"])
        self.assertIsNone(resp["question_actuelle"])
        self.assertNotIn("quelle ville", contenu)
        self.assertNotIn("dans quelle ville", contenu)
# -- Test : le prompt Dify connaît le profil et interdit le questionnaire --
    def test_dify_prompt_uses_known_profile_and_no_missing_field(self):
        resp, inputs = self._dify("Je cherche un emploi de développeur à Casablanca")
        prompt = inputs["system_prompt"]

        self.assertTrue(inputs.get("recommendations"))
        self.assertIn("PROFIL UTILISATEUR", prompt)
        self.assertIn("Casablanca", prompt)
        self.assertIn("PAS DE LISTES À PUCES INUTILES", prompt)
        self.assertNotIn("CHAMP MANQUANT UNIQUE", prompt)
        self.assertIn("RECOMMANDATIONS", prompt)
        self.assertTrue(resp["aides_recommandees"])

    # -- Test : le prompt Dify interdit la collecte de profil à la salutation --
    def test_dify_prompt_greeting_forbids_profile_question(self):
        user_no_location = _make_user(
            self.db, email="greet@example.com", ville="", region=""
        )
        _, inputs = self._dify("Bonjour", user=user_no_location)
        prompt = inputs["system_prompt"]

        self.assertIn("CONSIGNE SOCIALE", prompt)
        self.assertNotIn("CHAMP MANQUANT UNIQUE", prompt)
        self.assertIn("aucune question de profil", prompt.lower())

    # -- Test : « Explique-moi mieux » → pas de questionnaire répété -------
    def test_explain_more_does_not_restart_questionnaire(self):
        r1, _ = self._dify("Je cherche un emploi de développeur")
        _, inputs2 = self._dify(
            "Explique-moi mieux", historique_id=r1["historique_id"]
        )
        prompt2 = inputs2["system_prompt"]

        self.assertNotIn("CHAMP MANQUANT UNIQUE", prompt2)
        self.assertNotIn("recommendations", inputs2)
        self.assertIn("recherche en cours", prompt2)

    # -- Test : le résumé de profil distingue handicap oui/non ------------
    def test_dify_prompt_profile_summary_handicap_not_false_positive(self):
        _, inputs = self._dify("Je cherche un emploi de développeur")
        prompt = inputs["system_prompt"]

        # L'utilisateur de test n'a pas de handicap : ne jamais afficher « oui ».
        if "situation de handicap" in prompt:
            self.assertNotIn("situation de handicap : oui", prompt)
        # Le profil est bien passé au modèle.
        self.assertIn("PROFIL UTILISATEUR", prompt)

    # -- Test : metadata de streaming — salutation sans question -----------
    def test_streaming_greeting_metadata_no_question(self):
        user_no_location = _make_user(
            self.db,
            email="streamgreet@example.com",
            ville="",
            region="",
            niveau_etude="",
            statut_socio_pro="",
        )
        events, done = self._stream_events("Bonjour", user=user_no_location)
        self.assertIn("chunk", [e.get("type") for e in events])
        self.assertIn("done", [e.get("type") for e in events])
        data = done[0]
        # Même si la localisation manque, une salutation ne pose PAS de question.
        self.assertEqual(data["champs_manquants"], ["ville"])
        self.assertIsNone(data["question_actuelle"])

    # -- Test : metadata de streaming — UNE seule question quand il faut ----
    def test_streaming_job_metadata_single_question(self):
        user_no_location = _make_user(
            self.db,
            email="stream1@example.com",
            ville="",
            region="",
            niveau_etude="Licence",
            statut_socio_pro="Demandeur d'emploi",
        )
        events, done = self._stream_events("Je cherche un emploi", user=user_no_location)
        data = done[0]
        contenu = data["bot_message"]["contenu"]
        self.assertEqual(data["champs_manquants"], ["ville"])
        self.assertIn("ville", (data["question_actuelle"] or "").lower())
        self.assertEqual(contenu.count("?"), 1)

    def _stream_events(self, message, user=None):
        target = user or self.user

        async def _run():
            with patch("app.services.response_generator.dify_client") as mock_dify:
                def fake_stream(message, conversation_id=None, inputs=None):
                    yield {"success": False, "error": "boom", "raw": {}}
                mock_dify.send_message_stream.side_effect = fake_stream
                events, done = [], []
                async for ev in chat_service.handle_message_stream(
                    self.db, target, message
                ):
                    events.append(ev)
                    if ev.get("type") == "done":
                        done.append(ev["data"])
                return events, done

        return asyncio.run(_run())

    # -- Test : comportement du recommendation_engine conservé -------------
    def test_recommendation_engine_behavior_unchanged(self):
        profile = {
            "ville": "Casablanca",
            "region": "Casablanca-Settat",
            "niveau_etude": "Licence",
            "statut_socio_pro": "Demandeur d'emploi",
            "age": 21,
            "handicap": False,
        }
        recos = recommendation_engine.get_recommendations(
            self.db, profile, limit=5, keywords=["développeur"]
        )
        self.assertTrue(recos)
        top = recos[0]
        self.assertIn("Développeur", top["titre"], "Le mot-clé doit booster le ranking")
        self.assertEqual(top["url_officielle"], top["lien_officiel"])
        self.assertEqual(
            top["url_officielle"], "https://anapec.ma/chercheurs/offres"
        )
        for key in ("aide_id", "titre", "score_matching", "source"):
            self.assertIn(key, top)

        # Classement sans mot-clé : Casablanca d'abord (région compatible).
        recos_no_kw = recommendation_engine.get_recommendations(self.db, profile, limit=5)
        self.assertTrue(recos_no_kw)
        self.assertEqual(recos_no_kw[0].get("region_cible"), "Casablanca")

    # -- Test : « Que connais-tu de mon profil ? » → naturel, sans liste ---
    def test_ask_profile_response_is_natural_without_bullets(self):
        resp = self._fallback("Que connais-tu de mon profil ?")
        contenu = resp["bot_message"]["contenu"]

        self.assertIn("je sais de toi", contenu.lower())
        self.assertIn("Casablanca", contenu)
        self.assertEqual(_bullet_lines(contenu), 0)
        self._assert_no_french(contenu)


if __name__ == "__main__":
    unittest.main()