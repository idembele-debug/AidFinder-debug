"""
Response generator for AidFinder.

La génération de texte est assurée par Dify (via dify_client).
Le backend décide d'abord si des recommandations sont nécessaires
(profil complet + intention pertinente), puis effectue UN SEUL appel
Dify qui reçoit profil, contexte, historique et recommandations.
Si Dify est indisponible, ConversationFallback produit la réponse.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from app.services.conversation_engine import (
    ConversationDecision,
    ConversationMeta,
    ConversationState,
    IntentCategory,
)
from app.services.dify_client import dify_client

logger = logging.getLogger("aidfinder.response_generator")


# ─── Prompt builder ─────────────────────────────────────────────────────

class PromptBuilder:
    """Builds the full context prompt for the LLM."""

    HISTORY_TEMPLATE = (
        "Voici l'historique de la conversation :\n{history}\n"
    )
    RECOMMENDATIONS_TEMPLATE = (
        "\nVoici les aides disponibles recommandées (JSON) :\n{aids}\n"
    )

    SYSTEM_PROMPT = (
        "Tu es AidFinder, un assistant conversationnel marocain, chaleureux et direct, "
        "qui aide les utilisateurs à trouver des offres d'emploi, des aides sociales "
        "et des opportunités AU MAROC.\n\n"
        "RÈGLES D'OR — APPLIQUE-LES À CHAQUE RÉPONSE :\n"
        "1. CONVERSATION, PAS FORMULAIRE. Ne demande JAMAIS plus d'UNE information par "
        "message, et uniquement quand elle est réellement nécessaire pour avancer. "
        "Ne transforme jamais un échange en questionnaire.\n"
        "2. COURT ET NATUREL. Réponds en quelques phrases, au tutoiement (« tu »). "
        "Ne produis JAMAIS de guides complets ni de conseils génériques non demandés "
        "(CV, LinkedIn, GitHub, portfolio, lettre de motivation, démarches, sites de "
        "candidature…). Donne ce genre de conseils uniquement si l'utilisateur les "
        "demande explicitement.\n"
        "3. PAS DE LISTES À PUCES INUTILES. Utilise des listes uniquement pour présenter "
        "plusieurs offres ou plusieurs options distinctes. Dans un échange normal, "
        "rédige des phrases simples.\n"
        "4. UTILISE CE QUE TU SAIS DÉJÀ. Le profil utilisateur et l'historique sont "
        "fournis dans le contexte. Ne redemande JAMAIS une information déjà connue "
        "(ville, région, âge, niveau d'étude, statut…).\n"
        "5. CONTEXTE MAROCAIN UNIQUEMENT. AidFinder est une plateforme marocaine et le "
        "contexte actuel concerne principalement les offres d'emploi marocaines. "
        "La seule source d'offres est la base AidFinder, alimentée par ANAPEC "
        "(https://anapec.ma). N'invoque JAMAIS d'organismes, plateformes ou aides "
        "français(es) ou étranger(ère)s : France Travail, Pôle emploi, APEC, Mission "
        "Locale, CROUS, Indeed, LinkedIn Jobs, HelloWork, aide au logement française, "
        "titre de séjour, etc.\n"
        "6. JAMAIS D'INVENTION. N'invente aucune offre ni aide. Utilise uniquement les "
        "offres fournies dans la section RECOMMANDATIONS du contexte, ou explique "
        "honnêtement qu'aucune offre correspondante n'a été trouvée.\n"
        "7. ÉMOJIS AVEC PARCIMONIE (👋 😊 👍 🇲🇦).\n"
        "8. DONNE ENVIE DE CONTINUER. Termine par une question ouverte courte ou une "
        "proposition simple, sans jamais enchaîner plusieurs questions.\n\n"
    )

    SOCIAL_INTENTS = {
        IntentCategory.GREETING,
        IntentCategory.HOW_ARE_YOU,
        IntentCategory.THANKS,
        IntentCategory.GOODBYE,
        IntentCategory.HELP,
    }
    SEARCH_INTENTS = {
        IntentCategory.SEARCH_JOB,
        IntentCategory.SEARCH_STUDY,
        IntentCategory.SEARCH_HOUSING,
        IntentCategory.SEARCH_HEALTH,
        IntentCategory.SEARCH_BUSINESS,
    }

    @staticmethod
    def _profile_summary(profile: dict) -> str:
        """Résumé lisible du profil pour que l'IA ne redemande jamais ce qui est connu."""
        labels = {
            "ville": "ville",
            "region": "région",
            "niveau_etude": "niveau d'étude",
            "statut_socio_pro": "statut",
            "age": "âge",
            "handicap": "situation de handicap",
        }
        known = []
        for field in ("ville", "region", "niveau_etude", "statut_socio_pro", "age", "handicap"):
            value = profile.get(field)
            if value is None or value == "":
                continue
            if field == "handicap":
                known.append(
                    "situation de handicap : oui" if value is True
                    else "situation de handicap : non"
                )
            elif field == "age":
                known.append(f"âge : {value} ans")
            else:
                known.append(f"{labels.get(field, field)} : {value}")
        if not known:
            return "Aucune information de profil connue pour le moment."
        if len(known) == 1:
            return known[0].capitalize() + "."
        return ", ".join(known[:-1]).capitalize() + " et " + known[-1] + "."

    def build_system_prompt(
        self,
        decision: ConversationDecision,
        meta: ConversationMeta,
        history: list[dict] | None = None,
        recommendations: list[dict] | None = None,
    ) -> str:
        parts = [self.SYSTEM_PROMPT]

        # Profil utilisateur — tout ce qui est déjà connu, à ne jamais redemander.
        parts.append(
            "PROFIL UTILISATEUR (informations déjà connues, à NE JAMAIS redemander) :\n"
            f"{self._profile_summary(decision.merged_profile)}\n"
        )

        # État & intention du tour courant (purement contextuel).
        parts.append(f"État conversationnel : {decision.new_state.value}")
        parts.append(f"Intention détectée : {decision.intent.value}")

        # Collecte ciblée : UN SEUL champ manquant, une seule question, rien d'autre.
        if decision.should_ask_question and decision.field_to_ask:
            field_label = decision.field_to_ask.replace("_", " ")
            parts.append(
                f"CHAMP MANQUANT UNIQUE : « {field_label} ». Pose UNIQUEMENT la question "
                "correspondant à ce champ (une seule question), puis n'ajoute rien d'autre.\n"
            )
        elif decision.field_to_ask:
            parts.append(
                f"Note : le champ « {decision.field_to_ask.replace('_', ' ')} » manque, "
                "mais NE le demande pas à ce tour de conversation.\n"
            )

        # Échanges sociaux : brièveté exigée, aucune collecte de profil.
        if decision.intent in self.SOCIAL_INTENTS:
            parts.append(
                "CONSIGNE SOCIALE : l'utilisateur vient de te saluer ou d'échanger un "
                "message amical. Réponds-en une ou deux phrases chaleureuses et demande-lui "
                "ce qu'il cherche aujourd'hui. Ne pose AUCUNE question de profil et ne "
                "donne AUCUNE information non demandée.\n"
            )

        # Historique récent pour la continuité (jamais de question déjà répondues).
        if history:
            history_str = "\n".join(
                f"{'Utilisateur' if m['role'] == 'user' else 'AidFinder'} : "
                f"{m['content']}"
                for m in history[-10:]
            )
            parts.append(self.HISTORY_TEMPLATE.format(history=history_str))

        # Recommandations calculées par le backend : les présenter simplement.
        if recommendations:
            aids_json = json.dumps(
                [
                    {
                        "titre": r["titre"],
                        "description": r.get("description", ""),
                        "categorie": r.get("categorie", ""),
                        "score_matching": r.get("score_matching", 0),
                        "raisons": r.get("raisons", []),
                        "region_cible": r.get("region_cible"),
                        "niveau_etude_requis": r.get("niveau_etude_requis"),
                        "statut_socio_pro_requis": r.get("statut_socio_pro_requis"),
                        "age_min": r.get("age_min"),
                        "age_max": r.get("age_max"),
                        "handicap_requis": r.get("handicap_requis"),
                        "lien_officiel": r.get("lien_officiel"),
                    }
                    for r in recommendations
                ],
                default=str,
                ensure_ascii=False,
            )
            parts.append(self.RECOMMENDATIONS_TEMPLATE.format(aids=aids_json))
            parts.append(
                "INSTRUCTION : ces recommandations sont de VRAIES offres/aides marocaines "
                "calculées par le backend à partir du profil utilisateur. Présente-les de "
                "manière naturelle et concise : une phrase d'introduction puis une courte "
                "liste des offres (titre + lien officiel « Consulter »), puis une question "
                "ouverte finale (une seule). Utilise UNIQUEMENT les offres listées "
                "ci-dessus. N'ajoute AUCUN conseil de candidature (CV, LinkedIn, GitHub…), "
                "et AUCUNE plateforme externe.\n"
            )
            parts.append(
                "Réponds maintenant en présentant ces recommandations, chaleureusement "
                "et en restant bref."
            )
        elif decision.intent in self.SEARCH_INTENTS or decision.intent == IntentCategory.ASK_DETAILS:
            parts.append(
                "CONSIGNE (recherche en cours) : l'utilisateur cherche des opportunités "
                "marocaines concrètes. "
                "Si un champ bloquant manque (indiqué plus haut), pose UNIQUEMENT la "
                "question correspondante, en une phrase. Sinon, accueille sa demande en "
                "une phrase, pose AU PLUS UNE question d'affinage réellement utile "
                "(spécialisation, type de contrat, ville…), ou annonce une recherche "
                "d'offres. Ne pose JAMAIS plusieurs questions d'un coup et ne lance AUCUN "
                "guide complet. Ne cite AUCUNE plateforme française ou étrangère. Si des "
                "offres ont déjà été présentées précédemment, rappelle-le brièvement et "
                "propose une suite simple.\n"
            )
        else:
            parts.append(
                "CONSIGNE DU TOUR : réponds naturellement et brièvement au message. "
                "Si une information est réellement nécessaire pour avancer, pose UNE "
                "seule question courte. Sinon, continue la conversation sans collecter "
                "de données et sans liste.\n"
            )

        return "\n".join(parts)

    def build_messages(
        self,
        decision: ConversationDecision,
        meta: ConversationMeta,
        user_message: str,
        history: list[dict] | None = None,
        recommendations: list[dict] | None = None,
    ) -> list[dict]:
        system = self.build_system_prompt(decision, meta, history, recommendations)
        logger.debug("[PROMPT] System prompt construit (%d caractères)", len(system))
        return [
            {"role": "system", "content": system},
            {"role": "user", "content": user_message},
        ]


# ─── Fallback: conversation engine (LLM unavailable) ───────────────────

class ConversationFallback:
    """
    Fallback engine that uses the existing conversation state machine
    to produce responses when the LLM is unavailable.
    """

    def generate(
        self,
        decision: ConversationDecision,
        meta: ConversationMeta,
        history: list[dict] | None = None,
        recommendations: list[dict] | None = None,
    ) -> str:
        logger.warning("[FALLBACK] LLM indisponible — utilisation du moteur de fallback")
        state = decision.new_state
        intent = decision.intent

        # ── Greeting / social conversation ──────────────────────────
        if intent in (IntentCategory.GREETING, IntentCategory.HOW_ARE_YOU, IntentCategory.HELP):
            logger.info("[FALLBACK] Intention sociale détectée: %s", intent.value)
            return self._greeting_response(state, intent, decision)

        if intent == IntentCategory.THANKS:
            logger.info("[FALLBACK] Intention merci")
            return self._thanks_response()

        if intent == IntentCategory.GOODBYE:
            logger.info("[FALLBACK] Intention au revoir")
            return self._goodbye_response()

        # ── Profile query ───────────────────────────────────────────
        if intent == IntentCategory.ASK_PROFILE:
            logger.info("[FALLBACK] Demande de profil")
            return self._profile_response(decision.merged_profile)

        # ── Recommendations ─────────────────────────────────────────
        if recommendations:
            logger.info("[FALLBACK] Recommendations disponibles — %d aide(s)", len(recommendations))
            return self._recommendation_response(recommendations)

        # ── Collecting info / asking question (une seule question) ──
        if decision.should_ask_question and decision.field_to_ask:
            logger.info("[FALLBACK] Champ manquant: %s", decision.field_to_ask)
            from app.services.conversation_brain import ProfileCollector
            collector = ProfileCollector()
            return collector.get_question(decision.field_to_ask)

        # ── Recherche d'emploi sans offre disponible ────────────────
        if intent == IntentCategory.SEARCH_JOB:
            logger.info("[FALLBACK] Recherche d'emploi sans offre en base")
            return (
                "Je n'ai pas trouvé d'offre correspondant exactement à ta recherche "
                "pour le moment 📋. Tu peux reformuler ou préciser (ville, métier) ? "
                "Le portail ANAPEC (https://anapec.ma) est aussi mis à jour régulièrement."
            )

        # ── Clarification ───────────────────────────────────────────
        if decision.clarification_needed:
            logger.info("[FALLBACK] Clarification nécessaire")
            return (
                "Je n'ai pas bien compris ta demande 🤔 Tu cherches un emploi, "
                "une formation, un logement ou autre chose ?"
            )

        # ── Default ─────────────────────────────────────────────────
        logger.info("[FALLBACK] Réponse par défaut (aucun cas spécifique)")
        return (
            "Je suis AidFinder, ton assistant pour trouver des aides et des "
            "offres d'emploi au Maroc 🇲🇦 Qu'est-ce que tu cherches ?"
        )

    def _greeting_response(self, state: ConversationState, intent: IntentCategory,
                           decision: ConversationDecision) -> str:
        if intent == IntentCategory.HOW_ARE_YOU:
            return (
                "Je vais très bien, merci 😊 Et toi, tu cherches quelque chose "
                "aujourd'hui ?"
            )
        if intent == IntentCategory.HELP:
            return (
                "Je suis AidFinder, ton assistant marocain pour trouver des offres "
                "d'emploi, des aides et des opportunités 🇲🇦\n\n"
                "Dis-moi simplement ce que tu cherches, on commence par là."
            )
        return (
            "Bonjour 👋 Bienvenue sur AidFinder ! Tu cherches une aide, une offre "
            "d'emploi ou un accompagnement en particulier ?"
        )

    def _thanks_response(self) -> str:
        return (
            "Avec plaisir 😊 N'hésite pas si tu as d'autres questions, je suis là."
        )

    def _goodbye_response(self) -> str:
        return (
            "Au revoir et bonne journée 👋 Reviens quand tu veux sur AidFinder, "
            "à bientôt !"
        )

    def _profile_response(self, profile: dict) -> str:
        known = []
        for key in ("ville", "region", "niveau_etude", "statut_socio_pro", "age", "handicap"):
            value = profile.get(key)
            if not value:
                continue
            if key == "handicap":
                known.append("situation de handicap reconnue")
            elif key == "age":
                known.append(f"{value} ans")
            elif key == "ville":
                known.append(f"à {value}")
            elif key == "region":
                known.append(f"dans la région {value}")
            elif key == "niveau_etude":
                known.append(f"niveau {value}")
            else:
                known.append(str(value))
        if not known:
            return (
                "Je ne connais pas encore ton profil 😊 Si tu veux, complète-le "
                "dans la page Profil pour des recommandations plus précises."
            )
        base = "Voici ce que je sais de toi : " + ", ".join(known) + "."
        return (
            f"{base} Tu peux compléter ton profil à tout moment pour "
            "affiner les recommandations."
        )

    def _recommendation_response(self, recommendations: list[dict]) -> str:
        shown = recommendations[:3]
        lines = []
        for i, reco in enumerate(shown, 1):
            link = reco.get("lien_officiel") or reco.get("url_officielle") or ""
            titre = reco.get("titre", "Offre disponible")
            score = reco.get("score_matching", 0)
            ligne = f"{i}. {titre} — compatibilité {score}/100"
            if link:
                ligne += f"\n   🔗 {link}"
            lines.append(ligne)
        return (
            "Voici des offres qui correspondent bien à ta recherche :\n\n"
            f"{chr(10).join(lines)}\n\n"
            "Clique sur « Consulter » pour accéder à l'offre officielle. "
            "Tu veux affiner ou est-ce que ça te convient ?"
        )


# ─── Main ResponseGenerator ────────────────────────────────────────────

class ResponseGenerator:
    """
    LLM-first response generator using Dify.
    Tries: Dify → ConversationFallback
    """

    def __init__(self) -> None:
        self.prompt_builder = PromptBuilder()
        self.fallback = ConversationFallback()

    def _build_dify_inputs(
        self,
        system_prompt: str,
        decision: ConversationDecision,
        meta: ConversationMeta,
        history: list[dict] | None = None,
        recommendations: list[dict] | None = None,
    ) -> dict[str, Any]:
        """
        Build inputs dict for Dify containing system prompt, profile, and context.

        Only reuses existing data from decision, meta, and history.
        """
        inputs = {
            "system_prompt": system_prompt,
            "profile": decision.merged_profile,
            "state": decision.new_state.value,
            "intent": decision.intent.value,
        }

        # Add history if available
        if history:
            inputs["history"] = history

        # Add recommendations if available
        if recommendations:
            inputs["recommendations"] = recommendations

        return inputs

    def _get_conversation_id(self, meta: ConversationMeta) -> str | None:
        """Extract Dify conversation_id from meta if available."""
        return getattr(meta, 'dify_conversation_id', None)

    def generate(
        self,
        decision: ConversationDecision,
        meta: ConversationMeta,
        user_message: str,
        history: list[dict] | None = None,
        recommendations: list[dict] | None = None,
    ) -> str:
        logger.info("[GENERATE] Début — appel Dify (avec recommendations=%s)",
                     "oui" if recommendations else "non")

        if recommendations:
            logger.info("[GENERATE] Recommendations fournies en entrée: %d aide(s)",
                         len(recommendations))
        else:
            logger.info("[GENERATE] Pas de recommendations — Dify répond librement")

        # Build system prompt using PromptBuilder
        logger.info("[GENERATE] Construction du system prompt")
        system_prompt = self.prompt_builder.build_system_prompt(
            decision, meta, history, recommendations
        )
        
        # Build inputs dict with profile and context
        dify_inputs = self._build_dify_inputs(
            system_prompt, decision, meta, history, recommendations
        )
        logger.info("[GENERATE] Dify inputs — clés transmises: %s",
                     ", ".join(sorted(dify_inputs.keys())))
        logger.info("[GENERATE] system_prompt envoyé à Dify (%d caractères): %s...",
                     len(system_prompt), system_prompt[:150].replace("\n", " "))
        
        # Get existing conversation_id if available
        conversation_id = self._get_conversation_id(meta)
        logger.debug("[GENERATE] conversation_id=%s", conversation_id or "(new)")
        
        # Call Dify with query (last message), inputs, and conversation_id
        logger.debug("[GENERATE] Envoi à Dify — query: %s...", user_message[:50])
        result = dify_client.send_message(
            message=user_message,
            conversation_id=conversation_id,
            inputs=dify_inputs,
        )
        
        if result.get("success"):
            response = result.get("answer", "").strip()
            if response:
                # Store new conversation_id if received
                received_conversation_id = result.get("conversation_id")
                if received_conversation_id:
                    logger.debug("[GENERATE] conversation_id reçue: %s", received_conversation_id)
                    meta.dify_conversation_id = received_conversation_id
                
                logger.info("[GENERATE] Réponse Dify obtenue (%d caractères)", len(response))
                logger.info("[CHAT] PROVIDER=DIFY")
                return response
            logger.warning("[GENERATE] Dify a retourné une réponse vide")
        else:
            error_msg = result.get("error", "Erreur Dify inconnue")
            logger.error("[GENERATE] Dify a échoué: %s", error_msg)

        # Fallback to conversation engine
        logger.warning("[GENERATE] UTILISATION DU FALLBACK — Dify indisponible ou réponse vide")
        logger.info("[CHAT] PROVIDER=LOCAL_FALLBACK")
        logger.info("[CHAT] USING_LOCAL_FALLBACK")
        return self.fallback.generate(decision, meta, history, recommendations)

    async def generate_stream(
        self,
        decision: ConversationDecision,
        meta: ConversationMeta,
        user_message: str,
        history: list[dict] | None = None,
        recommendations: list[dict] | None = None,
    ):
        """Async generator yielding response text chunks."""
        logger.info("[STREAM] Début stream (avec recommendations=%s)",
                     "oui" if recommendations else "non")

        # Build system prompt using PromptBuilder
        system_prompt = self.prompt_builder.build_system_prompt(
            decision, meta, history, recommendations
        )
        
        # Build inputs dict with profile and context
        dify_inputs = self._build_dify_inputs(
            system_prompt, decision, meta, history, recommendations
        )
        logger.info("[STREAM] Dify inputs — clés transmises: %s",
                     ", ".join(sorted(dify_inputs.keys())))
        logger.info("[STREAM] system_prompt envoyé à Dify (%d caractères): %s...",
                     len(system_prompt), system_prompt[:150].replace("\n", " "))
        
        # Get existing conversation_id if available
        conversation_id = self._get_conversation_id(meta)
        logger.debug("[STREAM] conversation_id=%s", conversation_id or "(new)")
        
        logger.info("[STREAM] Stream Dify démarré")
        stream_failed = False
        chunk_count = 0
        
        try:
            for event in dify_client.send_message_stream(
                message=user_message,
                conversation_id=conversation_id,
                inputs=dify_inputs,
            ):
                if not event.get("success"):
                    logger.warning("[STREAM] Erreur stream: %s", event.get("error"))
                    stream_failed = True
                    break
                
                # Extract answer from event — transmis tel quel par Dify,
                # sans .strip(), pour préserver les espaces de début/fin
                # de chaque chunk lors de leur concaténation.
                answer = event.get("answer", "")
                if answer:
                    chunk_count += 1
                    yield answer
                
                # Store conversation_id if received (uniforme: toujours mettre à jour)
                received_conversation_id = event.get("conversation_id")
                if received_conversation_id:
                    logger.debug("[STREAM] conversation_id reçue: %s", received_conversation_id)
                    meta.dify_conversation_id = received_conversation_id
        except Exception as e:
            logger.error("[STREAM] Exception stream: %s", e)
            stream_failed = True
        
        if stream_failed or chunk_count == 0:
            logger.warning("[STREAM] Stream échoué ou vide — fallback")
            logger.info("[CHAT] PROVIDER=LOCAL_FALLBACK")
            logger.info("[CHAT] USING_LOCAL_FALLBACK")
            text = self.fallback.generate(decision, meta, history, recommendations)
            yield text
        else:
            logger.info("[STREAM] Stream terminé — %d chunks envoyés", chunk_count)
            logger.info("[CHAT] PROVIDER=DIFY")

# Singleton
response_generator = ResponseGenerator()