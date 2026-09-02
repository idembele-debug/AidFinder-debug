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
        "Tu es AidFinder, un assistant conversationnel spécialisé dans l'orientation "
        "vers les aides financières, les aides sociales et les offres d'emploi AU MAROC.\n\n"
        "CONTEXTE GÉOGRAPHIQUE OBLIGATOIRE :\n"
        "- AidFinder est une plateforme MAROCAINE. Tous les organismes, aides et offres "
        "cités sont marocains (ANAPEC, etc.).\n"
        "- N'utilise JAMAIS d'organismes, de sites ou de plateformes français, belges, "
        "canadiens ou internationaux (France Travail, Pôle emploi, Apec, Indeed, "
        "LinkedIn Jobs, HelloWork, CROUS…) comme réponse, suggestion ou référence.\n"
        "- Pour les offres d'emploi, la seule source à mentionner est la base AidFinder "
        "alimentée par ANAPEC (https://anapec.ma).\n\n"
        "RÈGLES STRICTES :\n"
        "1. Tu réponds TOUJOURS de manière naturelle et chaleureuse, comme un vrai conseiller.\n"
        "2. Tu n'inventes JAMAIS une aide ou une offre qui n'est pas dans la liste fournie.\n"
        "3. Quand des offres/aides recommandées sont fournies en JSON, présente-les de façon "
        "courte et invite à consulter le lien officiel. NE les remplace PAS par une liste "
        "générique de sites externes.\n"
        "4. Si l'utilisateur demande des informations que tu n'as pas, dis-le honnêtement.\n"
        "5. Tu poses UNE SEULE question à la fois, UNIQUEMENT sur le champ manquant indiqué.\n"
        "6. Utilise les émojis avec parcimonie (👋 😊 👍).\n"
        "7. Si l'utilisateur donne une information, remercie-le et passe à l'étape suivante.\n"
        "8. Si l'utilisateur te salue (bonjour, salut, etc.), réponds de manière naturelle "
        "et demande-lui ce qu'il cherche.\n"
        "9. Ne redemande jamais une information déjà présente dans le profil utilisateur.\n"
        "10. Tu es AidFinder, un assistant marocain, pas un assistant générique.\n\n"
    )

    def build_system_prompt(
        self,
        decision: ConversationDecision,
        meta: ConversationMeta,
        history: list[dict] | None = None,
        recommendations: list[dict] | None = None,
    ) -> str:
        profile_str = json.dumps(decision.merged_profile, default=str, ensure_ascii=False)

        parts = [self.SYSTEM_PROMPT]

        # User profile (for context only — LLM decides what to ask)
        parts.append(f"Profil utilisateur (connu jusqu'à présent) : {profile_str}\n")

        # Conversation state (informational only)
        parts.append(f"État conversationnel : {decision.new_state.value}\n")
        parts.append(f"Intention détectée : {decision.intent.value}\n")

        # Champ manquant unique à demander (collecte ciblée — jamais de questionnaire complet)
        if decision.should_ask_question and decision.field_to_ask:
            field_label = decision.field_to_ask.replace("_", " ")
            parts.append(
                f"CHAMP MANQUANT UNIQUE : « {field_label} ». Pose UNIQUEMENT la question "
                "correspondant à ce champ (une seule question), puis n'ajoute rien d'autre.\n"
            )

        # History
        if history:
            history_str = "\n".join(
                f"{'Utilisateur' if m['role'] == 'user' else 'AidFinder'} : "
                f"{m['content']}"
                for m in history[-10:]
            )
            parts.append(self.HISTORY_TEMPLATE.format(history=history_str))

        # Recommendations (fournies par le backend — jamais inventées par Dify)
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
                "\n\nINSTRUCTION : Ces recommandations sont des offres/aides marocaines "
                "réelles calculées par le backend à partir du profil utilisateur. "
                "Présente-les à l'utilisateur de manière naturelle et personnalisée. "
                "Utilise UNIQUEMENT les offres listées ci-dessus ; n'en invente aucune. "
                "Ne mentionne AUCUN site externe français ou étranger. Organise la réponse "
                "ainsi :\n"
                "1. Réponds d'abord naturellement au message de l'utilisateur.\n"
                "2. Ensuite, présente clairement les offres recommandées, avec leur lien officiel.\n"
                "3. Termine par une question ouverte ou une proposition d'aide supplémentaire."
            )
            parts.append(
                "Réponds maintenant en présentant ces recommandations, de manière chaleureuse "
                "et concise."
            )
        else:
            extras: list[str] = []
            if decision.intent == IntentCategory.SEARCH_JOB:
                extras.append(
                    "Note : la demande concerne les offres d'emploi marocaines. "
                    "La seule source d'offres est la base AidFinder (ANAPEC). "
                    "Ne cite JAMAIS de plateformes françaises ou étrangères. "
                    "Si aucune offre n'est disponible, explique-le brièvement "
                    "et propose de reformuler la recherche."
                )
            parts.append(
                "Réponds maintenant au message de l'utilisateur de manière naturelle, "
                "chaleureuse et concise.\n\n"
                "Tu es libre de répondre comme un vrai conseiller. "
                "Ne pose des questions sur le profil que si le champ manquant est indiqué. "
                "Si l'utilisateur te salue, salue-le en retour. "
                "Si l'utilisateur te demande qui tu es, présente-toi. "
                "Si l'utilisateur commence à parler de sa situation, "
                "écoute et pose des questions pertinentes une par une."
            )
            if extras:
                parts.append("\n".join(extras))

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

        # ── Collecting info / asking question ───────────────────────
        if decision.field_to_ask:
            logger.info("[FALLBACK] Champ manquant: %s", decision.field_to_ask)
            from app.services.conversation_brain import ProfileCollector
            collector = ProfileCollector()
            return collector.get_question(decision.field_to_ask)

        # ── Recherche d'emploi sans offre disponible ────────────────
        if intent == IntentCategory.SEARCH_JOB:
            logger.info("[FALLBACK] Recherche d'emploi sans offre en base")
            return (
                "Je suis désolé, je n'ai pas trouvé d'offre d'emploi marocaine "
                "correspondant à votre recherche pour le moment. 📋\n\n"
                "Vous pouvez consulter régulièrement le portail ANAPEC "
                "(https://anapec.ma) ou tenter de reformuler votre recherche."
            )

        # ── Clarification ───────────────────────────────────────────
        if decision.clarification_needed:
            logger.info("[FALLBACK] Clarification nécessaire")
            return (
                "Je n'ai pas bien compris votre demande. 🤔\n\n"
                "Pouvez-vous reformuler ? Par exemple :\n"
                "• \"Je cherche un emploi\"\n"
                "• \"Je veux poursuivre mes études\"\n"
                "• \"J'ai besoin d'un logement\""
            )

        # ── Default ─────────────────────────────────────────────────
        logger.info("[FALLBACK] Réponse par défaut (aucun cas spécifique)")
        return (
            "Je suis là pour vous aider à trouver des aides "
            "financières et sociales adaptées à votre situation.\n\n"
            "Que recherchez-vous comme aide ?"
        )

    def _greeting_response(self, state: ConversationState, intent: IntentCategory,
                           decision: ConversationDecision) -> str:
        if intent == IntentCategory.HOW_ARE_YOU:
            return (
                "Je vais très bien, merci ! 😊\n\n"
                "Je suis AidFinder, votre assistant pour trouver "
                "des aides financières et sociales au Maroc.\n\n"
                "Que puis-je faire pour vous aujourd'hui ?"
            )
        if intent == IntentCategory.HELP:
            return (
                "Je suis AidFinder, votre assistant pour trouver des aides "
                "financières et sociales au Maroc. 🤖\n\n"
                "Je peux vous aider à :\n"
                "• Trouver des aides pour l'emploi, les études, le logement, la santé\n"
                "• Vérifier votre éligibilité aux différentes aides\n"
                "• Vous orienter vers les bons organismes\n\n"
                "Dites-moi ce que vous cherchez !"
            )
        return (
            "Bonjour 👋\n\n"
            "Je suis AidFinder. Je suis là pour vous accompagner "
            "dans la recherche des aides financières, des aides sociales "
            "et des offres d'emploi au Maroc. 🇲🇦\n\n"
            "Comment puis-je vous aider aujourd'hui ?"
        )

    def _thanks_response(self) -> str:
        return (
            "Avec plaisir ! 😊\n\n"
            "N'hésitez pas si vous avez d'autres questions, "
            "je suis là pour vous aider."
        )

    def _goodbye_response(self) -> str:
        return (
            "Au revoir et bonne journée ! 😊\n\n"
            "N'hésitez pas à revenir sur AidFinder "
            "si vous avez besoin d'aide. À bientôt !"
        )

    def _profile_response(self, profile: dict) -> str:
        filled = {k: v for k, v in profile.items() if v}
        missing = [
            f for f in ["ville", "region", "niveau_etude",
                        "statut_socio_pro", "age", "handicap"]
            if not profile.get(f)
        ]
        msg = "Voici ce que je sais de vous :\n\n"
        labels = {
            "ville": "Ville", "region": "Région",
            "niveau_etude": "Niveau d'étude",
            "statut_socio_pro": "Situation",
            "age": "Âge", "handicap": "Handicap",
        }
        for k, v in filled.items():
            msg += f"• {labels.get(k, k)} : {v}\n"
        if missing:
            missing_labels = [labels.get(f, f) for f in missing]
            msg += (
                f"\nIl me manque : {', '.join(missing_labels)}.\n"
                "Puis-je vous poser quelques questions pour mieux vous aider ?"
            )
        return msg

    def _recommendation_response(self, recommendations: list[dict]) -> str:
        shown = recommendations[:3]
        lines = []
        for i, reco in enumerate(shown, 1):
            link = reco.get("lien_officiel") or reco.get("url_officielle") or ""
            titre = reco.get("titre", "Offre disponible")
            raisons = ", ".join(reco.get("raisons", [])[:2])
            score = reco.get("score_matching", 0)
            ligne = f"{i}. **{titre}** — compatibilité {score}/100"
            if raisons:
                ligne += f" ({raisons})"
            if link:
                ligne += f"\n   🔗 {link}"
            lines.append(ligne)
        return (
            "Voici des offres d'emploi marocaines disponibles qui correspondent "
            f"à votre profil :\n\n{chr(10).join(lines)}\n\n"
            "Cliquez sur « Consulter » pour accéder à l'offre officielle. "
            "Souhaitez-vous plus de détails ou affiner la recherche ?"
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
                return response
            logger.warning("[GENERATE] Dify a retourné une réponse vide")
        else:
            error_msg = result.get("error", "Erreur Dify inconnue")
            logger.error("[GENERATE] Dify a échoué: %s", error_msg)

        # Fallback to conversation engine
        logger.warning("[GENERATE] UTILISATION DU FALLBACK — Dify indisponible ou réponse vide")
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
            text = self.fallback.generate(decision, meta, history, recommendations)
            yield text
        else:
            logger.info("[STREAM] Stream terminé — %d chunks envoyés", chunk_count)

# Singleton
response_generator = ResponseGenerator()