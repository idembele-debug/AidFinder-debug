# -*- coding: utf-8 -*-
"""Tests fonctionnels du chatbot — recherche d'emploi marocaine.

Reproduit les scénarios exigés (TEST 1 → 7) en utilisant le fallback
(Dify simulé en échec) pour obtenir des réponses déterministes, et vérifie
que le système :
- comprend la recherche d'emploi,
- utilise le profil sans reposer les questions déjà connues,
- ne produit PAS de liste générique française (France Travail, Apec…),
- recommande des offres marocaines de la base avec lien officiel cliquable
  (url_officielle / lien_officiel),
- ne demande qu'une seule question ciblée quand seule la localisation manque.
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
from app.models.aides import Aides
from app.models.utilisateurs import Utilisateur
from app.services.chat_service import chat_service


FORBIDDEN_FR_PLATFORMS = (
    "france travail",
    "pôle emploi",
    "pole emploi",
    "apec",
    "indeed",
    "linkedin jobs",
    "hellowork",
    "crous",
    "hello work",
)


def _make_user(session, **overrides):
    fields = {
        "nom": "Profil Complet",
        "email": "emploi@example.com",
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


def _make_aide(session, titre, region, niveau=None, entreprise=None):
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
        entreprise_nom=entreprise,
        lieu_travail=region,
        est_active=True,
        url_officielle="https://anapec.ma/chercheurs/offres",
    )
    session.add(aide)
    return aide


class ChatbotJobsMarocTestCase(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine(
            "sqlite:///:memory:", connect_args={"check_same_thread": False}
        )
        Base.metadata.create_all(bind=self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)
        self.db = self.SessionLocal()
        self.user = _make_user(self.db)

        # Base d'offres marocaines variées
        _make_aide(self.db, "Développeur Full-Stack", "Fès", niveau="Licence")
        _make_aide(self.db, "Comptable Confirmé", "Casablanca", niveau="Licence")
        _make_aide(self.db, "Responsable Ressources Humaines", "Rabat", niveau="Master")
        _make_aide(self.db, "Technicien de Maintenance", "Casablanca", niveau="Bac")
        self.db.commit()

    def tearDown(self):
        self.db.close()
        self.engine.dispose()

    def _fallback_response_for(self, message, user=None):
        target = user or self.user
        mock_dify = patch(
            "app.services.response_generator.dify_client"
        ).start()
        mock_dify.send_message = lambda *a, **k: {
            "success": False, "error": "boom", "raw": {}
        }
        try:
            return chat_service.handle_message(self.db, target, message)
        finally:
            patch.stopall()

    def _assert_no_french_platforms(self, contenu):
        """Vérifie l'absence de plateformes françaises, en évitant un faux
        positif sur `anapec.ma` (qui contient la sous-chaîne « apec »)."""
        nettoye = contenu.lower().replace("anapec", "aidfinder")
        for plateforme in FORBIDDEN_FR_PLATFORMS:
            self.assertNotIn(plateforme, nettoye, "Plateforme FR dans la réponse")

    # -- TEST 1 : Bonjour --------------------------------------------------
    def test_greeting_no_questionnaire_no_french_sites(self):
        resp = self._fallback_response_for("Bonjour")
        contenu = resp["bot_message"]["contenu"].lower()
        self.assertIn("aidfinder", contenu)
        self.assertFalse(resp["aides_recommandees"])
        self.assertIsNone(resp["question_actuelle"])
        self._assert_no_french_platforms(contenu)

    # -- TEST 2 : Je cherche une offre d'emploi ----------------------------
    def test_job_search_recommendations_from_base(self):
        resp = self._fallback_response_for("Je cherche une offre d'emploi")
        self.assertTrue(resp["aides_recommandees"], "Aucune offre recommandée")
        contenu = resp["bot_message"]["contenu"].lower()
        self.assertIn("consulter", contenu)
        self._assert_no_french_platforms(contenu)
        # Chaque reco expose une URL réelle et les deux clés attendues
        for reco in resp["aides_recommandees"]:
            self.assertTrue(reco.get("url_officielle"))
            self.assertEqual(reco["url_officielle"], reco["lien_officiel"])

    # -- TEST 3 : Je cherche un emploi à Casablanca ------------------------
    def test_job_search_casablanca(self):
        resp = self._fallback_response_for("Je cherche un emploi à Casablanca")
        self.assertTrue(resp["aides_recommandees"])
        contenu = resp["bot_message"]["contenu"].lower()
        self._assert_no_french_platforms(contenu)
# -- TEST 4 : niveau d'études déjà dans le profil ----------------------
    def test_level_used_without_question(self):
        resp = self._fallback_response_for(
            "Je cherche un emploi adapté à mon niveau d'études"
        )
        self.assertTrue(resp["aides_recommandees"])
        self.assertIsNone(resp["question_actuelle"])
        self.assertEqual(resp["champs_manquants"], [])

    # -- TEST 5 : profil âge + région uniquement ---------------------------
    def test_minimal_profile_age_region_sufficient(self):
        user_age_region = _make_user(
            self.db,
            email="minimal@example.com",
            nom="Minimal",
            ville=None,
            region="Casablanca-Settat",
            niveau_etude=None,
            statut_socio_pro=None,
            situation_handicap=None,
        )
        resp = self._fallback_response_for(
            "Je cherche une offre d'emploi", user=user_age_region
        )
        self.assertTrue(resp["aides_recommandees"])
        self.assertIsNone(resp["question_actuelle"])

    # -- TEST 6 : âge mais sans localisation -------------------------------
    def test_missing_location_asks_only_location(self):
        user_no_location = _make_user(
            self.db,
            email="noloc@example.com",
            nom="Sans Localisation",
            ville="",
            region="",
            niveau_etude="Licence",
            statut_socio_pro="Demandeur d'emploi",
        )
        resp = self._fallback_response_for(
            "Je cherche une offre d'emploi", user=user_no_location
        )
        self.assertFalse(resp["aides_recommandees"])
        self.assertEqual(resp["champs_manquants"], ["ville"])

        question = resp["question_actuelle"] or ""
        self.assertIn("ville", question.lower())
        # Pas de questionnaire complet sur niveau/statut/handicap
        for extra in ("niveau", "statut", "handicap"):
            self.assertNotIn(extra, question.lower())

    # -- TEST 7 : Je cherche un emploi de développeur ----------------------
    def test_keyword_developer_ranks_first(self):
        resp = self._fallback_response_for("Je cherche un emploi de développeur")
        self.assertTrue(resp["aides_recommandees"])
        top = resp["aides_recommandees"][0]
        self.assertIn("Développeur", top["titre"])

    # -- Vérification du prompt Dify : champ manquant unique ---------------
    def test_dify_prompt_asks_only_missing_field(self):
        user_no_location = _make_user(
            self.db,
            email="prompt@example.com",
            nom="Prompt",
            ville="",
            region="",
        )
        from app.services import response_generator as rg

        with patch.object(rg, "dify_client") as mock_dify:
            def fake_send(message, conversation_id=None, inputs=None):
                return {
                    "success": True,
                    "answer": "ok",
                    "conversation_id": "c1",
                    "raw": {},
                }

            mock_dify.send_message.side_effect = fake_send
            chat_service.handle_message(
                self.db, user_no_location, "Je cherche une offre d'emploi"
            )
            inputs = mock_dify.send_message.call_args
            inputs = inputs[1].get("inputs", {})
            system_prompt = inputs.get("system_prompt", "")
            self.assertIn("CHAMP MANQUANT UNIQUE", system_prompt)
            self.assertIn("ville", system_prompt)

    # -- Extraction des mots-clés ------------------------------------------
    def test_keyword_extraction(self):
        collector = chat_service.brain.profile_collector
        self.assertEqual(
            collector.extract_search_keywords("Je cherche un emploi de développeur"),
            ["développeur"],
        )
        self.assertEqual(
            collector.extract_search_keywords("Je cherche un emploi à Casablanca"),
            [],
        )
        self.assertEqual(
            collector.extract_search_keywords(
                "Je cherche un emploi adapté à mon niveau d'études"
            ),
            [],
        )


if __name__ == "__main__":
    unittest.main()