import logging
import re
from datetime import date
from typing import Any

from app.services.conversation_engine import (
    ConversationDecision,
    ConversationMeta,
    ConversationState,
    IntentCategory,
    StateMachine,
)

logger = logging.getLogger("aidfinder.conversation_brain")


class IntentDetector:
    PATTERNS: dict[IntentCategory, re.Pattern] = {
        IntentCategory.GREETING: re.compile(
            r"^(bonjour|salut|bonsoir|hello|coucou|hey|cc|salam|bsr|bonsoir)[\s!?.]*$",
            re.I,
        ),
        IntentCategory.HOW_ARE_YOU: re.compile(
            r"(comment\s*(?:vas|allez)\s*(?:tu|vous)?|comment\s*ça\s*va|ça\s*va\s*[?]?)",
            re.I,
        ),
        IntentCategory.SEARCH_JOB: re.compile(
            r"(emploi|travail|recrutement|job|carrière|chômage|pôle[-\s]emploi"
            r"|cherche\s*(?:un|du)\s*(?:emploi|travail)|offre\s*d['\']emploi)",
            re.I,
        ),
        IntentCategory.SEARCH_STUDY: re.compile(
            r"(étude|étudiant|bourse|formation|université|faculté|école"
            r"|diplôme|scolarité|stage|apprentissage|alternance)",
            re.I,
        ),
        IntentCategory.SEARCH_HOUSING: re.compile(
            r"(logement|appartement|maison|habitat|location|hébergement"
            r"|aide\s*au\s*logement|allocations?\s*logement)",
            re.I,
        ),
        IntentCategory.SEARCH_HEALTH: re.compile(
            r"(santé|médical|handicap|maladie|soin|mutuelle|assurance\s*maladie"
            r"|couverture\s*médicale|ramed|amostip)",
            re.I,
        ),
        IntentCategory.SEARCH_BUSINESS: re.compile(
            r"(entreprise|création|projet|financement|startup"
            r"|entrepreneur|business|indépendant|auto-entrepreneur)",
            re.I,
        ),
        IntentCategory.ASK_PROFILE: re.compile(
            r"(mon\s*profil|mes\s*informations|que\s*sais[-\s]tu"
            r"|quelles\s*infos|que\s*connais[-\s]tu)",
            re.I,
        ),
        IntentCategory.ASK_BEST: re.compile(
            r"(meilleur|mieux|top|priorité|le\s*plus\s*pertinent"
            r"|la\s*plus\s*pertinente|lequel|laquelle|recommander)",
            re.I,
        ),
        IntentCategory.ASK_DETAILS: re.compile(
            r"(détail|précision|plus\s*d['\"]infos?|explique"
            r"|comment\s*ça\s*marche|en\s*savoir\s*plus|développe)",
            re.I,
        ),
        IntentCategory.THANKS: re.compile(
            r"(merci|merci\s*beaucoup|merci\s*bien|je\s*te\s*remercie|merci\s*infiniement)",
            re.I,
        ),
        IntentCategory.GOODBYE: re.compile(
            r"(au\s*revoir|bye|à\s*plus|à\s*bientôt|ciao|adieu|bonne\s*journée)",
            re.I,
        ),
        IntentCategory.HELP: re.compile(
            r"(aide|que\s*fais[-\s]tu|comment\s*ça\s*marche"
            r"|à\s*quoi\s*ça\s*sert|comment\s*tu\s*fonctionnes)",
            re.I,
        ),
        IntentCategory.ASK_SPECIFIC_AID: re.compile(
            r"(aide\s+(?:appelée?|nommé|intitulé)|qu['\"]est-ce\s*que\s*"
            r"|c['\"]est\s*quoi|parle[-\s]moi\s*de)",
            re.I,
        ),
    }

    def detect(self, message: str, meta: ConversationMeta) -> IntentCategory:
        stripped = message.strip()

        # The LLM decides how to interpret the message — not the intent detector.
        # We only detect explicit intents for context tracking.
        for intent, pattern in self.PATTERNS.items():
            if pattern.search(stripped):
                return intent

        return IntentCategory.UNKNOWN


class ProfileCollector:
    REQUIRED_FIELDS = ["ville", "region", "niveau_etude", "statut_socio_pro", "age", "handicap"]

    EXTRACTION_PATTERNS: dict[str, re.Pattern] = {
        "ville": re.compile(
            r"(?:"
            r"j['\"]?habite\s+(?:à|dans|sur|près\s*de)\s+"
            r"|je\s+(?:vis|suis|travaille|recherche)\s+(?:à\s+)?"
            r"|je\s+cherche\s+(?:une\s+aide|un\s+emploi|un\s+logement|une\s+offre|du\s+travail)\s+(?:à\s+|dans\s+)?"
            r")"
            r"(Casablanca|Rabat|Tanger|Tétouan|Tetouan|Fès|Fes|Marrakech|Agadir|Oujda|Meknès|Meknes|Kenitra|Kénitra|Salé|Sale|Mohammedia|El\s*Jadida|Nador|Beni\s*Mellal|Laâyoune|Laayoune|Errachidia)",
            re.I,
        ),
        "region": re.compile(
            r"(?:région|region)\s*(?:de\s*)?([\w\s\-']+)", re.I
        ),
        "niveau_etude": re.compile(
            r"(sans\s*diplome|sans\s*diplôme|bac|baccalauréat|baccalaureat"
            r"|licence|master|doctorat|ingénieur|ingenieur"
            r"|bts|dut|cap|brevet|bac\+[0-9])",
            re.I,
        ),
        "statut_socio_pro": re.compile(
            r"(étudiant|etudiant|employé|employe|salarié|salarie"
            r"|demandeur\s*d['\"]?emploi|chômeur|chomeur"
            r"|indépendant|independant|retraité|retraite"
            r"|stagiaire|fonctionnaire|sans\s*emploi)",  # noqa: E501
            re.I,
        ),
        "age": re.compile(r"(?:j['\"]ai|âge|age)\s*(\d+)\s*(?:ans)", re.I),
        "handicap": re.compile(
            r"(?:handicap|situation\s*de\s*handicap|rqth|reconnaissance\s*handicap"
            r"|handicapé|handicapee|handicapée|aménagements?)",  # noqa: E501
            re.I,
        ),
    }

    QUESTIONS: dict[str, str] = {
        "ville": "Dans quelle ville habitez-vous ?",
        "region": "Dans quelle région se trouve votre ville ?",
        "niveau_etude": (
            "Quel est votre niveau d'étude ?\n\n"
            "Exemples : sans diplôme, bac, licence, master, doctorat"
        ),
        "statut_socio_pro": (
            "Quelle est votre situation actuelle ?\n\n"
            "Exemples : étudiant, employé, demandeur d'emploi, indépendant, retraité"
        ),
        "age": "Quel âge avez-vous ? (pour vérifier votre éligibilité aux aides)",
        "handicap": "Avez-vous une situation de handicap reconnue ?",
    }

    SUGGESTIONS: dict[str, list[str]] = {
        "ville": [
            "Casablanca",
            "Rabat",
            "Marrakech",
            "Fès",
            "Tanger",
            "Agadir",
            "Oujda",
            "Meknès",
        ],
        "region": [
            "Casablanca-Settat",
            "Rabat-Salé-Kénitra",
            "Marrakech-Safi",
            "Fès-Meknès",
            "Tanger-Tétouan-Al Hoceïma",
        ],
        "niveau_etude": [
            "Sans diplôme",
            "Bac",
            "Bac+2",
            "Licence",
            "Master",
            "Doctorat",
        ],
        "statut_socio_pro": [
            "Étudiant",
            "Employé",
            "Demandeur d'emploi",
            "Indépendant",
            "Retraité",
            "Stagiaire",
        ],
        "handicap": ["Oui", "Non"],
    }

    # Champs bloquants : âge + localisation (ville OU région).
    BLOCKING_AGE_FIELD = "age"
    BLOCKING_LOCATION_FIELDS = ("ville", "region")
    COLLECT_ORDER = ("ville", "age")
    AFFINAGE_FIELDS = ("niveau_etude", "statut_socio_pro", "handicap")

    # Mapping fiable ville -> région (ne jamais inventer pour une ville inconnue).
    VILLE_TO_REGION = {
        "casablanca": "Casablanca-Settat",
        "rabat": "Rabat-Salé-Kénitra",
        "sale": "Rabat-Salé-Kénitra",
        "kénitra": "Rabat-Salé-Kénitra",
        "kenitra": "Rabat-Salé-Kénitra",
        "fes": "Fès-Meknès",
        "fès": "Fès-Meknès",
        "meknes": "Fès-Meknès",
        "meknès": "Fès-Meknès",
        "marrakech": "Marrakech-Safi",
        "agadir": "Souss-Massa",
        "tanger": "Tanger-Tétouan-Al Hoceïma",
        "tétouan": "Tanger-Tétouan-Al Hoceïma",
        "oujda": "Oriental",
        "nador": "Oriental",
    }

    # Refus explicites uniquement.
    REFUSAL_PATTERNS = re.compile(
        r"(je\s+(?:(?:ne\s+)?(?:veux|souhaite|préfère)\s+pas|refuse)"
        r"|je\s+ne\s+(?:veux|souhaite|peux)\s+(?:pas|point)"
        r"|pas\s+(?:donner|dire|répondre)\s+(?:mon|.*)?(?:âge|age)"
        r"|on\s+peut\s+(?:passer|éviter)|sans\s+importance)",
        re.I,
    )

    # Mots exclus de l'extraction de mots-clés de recherche : filler français,
    # verbes d'intention, mots vagues et noms de lieux déjà gérés par le profil.
    SEARCH_KEYWORD_STOPWORDS = {
        "je", "tu", "il", "elle", "on", "nous", "vous", "ils", "elles",
        "cherche", "cherches", "cherchent", "chercher", "recherche",
        "recherches", "rechercher", "recherche", "veux", "voudrais",
        "souhaite", "souhaiterais", "aimerais", "veut", "peut", "peux",
        "pouvez", "pourriez", "pouvoir", "être", "etre", "est", "suis",
        "un", "une", "du", "de", "des", "le", "la", "les", "l", "d", "a",
        "à", "et", "ou", "pour", "dans", "sur", "avec", "sans", "vers",
        "près", "mon", "ma", "mes", "ton", "ta", "tes", "son", "sa", "ses",
        "notre", "votre", "leur", "leurs", "moi", "toi", "se", "ce",
        "emploi", "emplois", "travail", "travaille", "travailler", "job",
        "jobs", "offre", "offres", "poste", "postes", "métier", "metier",
        "carrière", "carriere", "recrutement", "stage", "stages",
        "alternance", "contrat", "temporaire", "cdd", "cdi", "intérim",
        "situation", "actuel", "actuelle", "actuellement", "bien", "très",
        "tres", "adapté", "adaptee", "adapte", "adaptés", "adaptees",
        "adaptes", "niveau", "niveaux", "étude", "etude", "études", "etudes",
        "scolaire", "faire", "trouver", "trouve", "trouveras", "trouver",
        "idéal", "ideal", "conseiller", "recommander", "recommande",
        "aider", "aide", "aides", "information", "informations", "info",
        "plus", "moins", "oui", "non", "svp", "merci", "bonjour", "salut",
        "bonsoir", "repondre", "répondre", "dire", "demander", "seconder",
    }

    def extract_search_keywords(self, message: str) -> list[str]:
        """Extrait des mots-clés de recherche depuis le message utilisateur.

        Exclut les mots de liaison français, les mots d'intention
        (emploi, offre, travail…) et les noms de lieux déjà portés par le
        profil. Ex. « Je cherche un emploi de développeur » → ['développeur'].
        """
        tokens = re.findall(r"[a-zA-ZÀ-ÿ]{3,}", message)
        known_places = {key.casefold() for key in self.VILLE_TO_REGION} | {
            region.casefold() for region in self.VILLE_TO_REGION.values()
        }
        keywords: list[str] = []
        for token in tokens:
            norm = token.casefold()
            if norm in self.SEARCH_KEYWORD_STOPWORDS:
                continue
            if norm in known_places:
                continue
            if norm not in keywords:
                keywords.append(norm)
        return keywords[:6]

    def extract(self, message: str) -> dict[str, Any]:
        extracted: dict[str, Any] = {}
        for field, pattern in self.EXTRACTION_PATTERNS.items():
            match = pattern.search(message)
            if not match:
                continue
            if field == "age":
                try:
                    extracted[field] = int(match.group(1))
                except (ValueError, IndexError):
                    pass
            elif field == "handicap":
                extracted[field] = True
            elif match.lastindex and match.group(1):
                extracted[field] = match.group(1).strip().capitalize()
            else:
                extracted[field] = match.group(0).strip().capitalize()
        return extracted

    def is_complete(self, profile: dict) -> bool:
        return all(
            profile.get(field) is not None and profile.get(field) != ""
            for field in self.REQUIRED_FIELDS
        )

    def missing_fields(self, profile: dict) -> list[str]:
        return [
            field
            for field in self.REQUIRED_FIELDS
            if profile.get(field) is None or profile.get(field) == ""
        ]

    def next_missing_field(self, profile: dict) -> str | None:
        for field in self.REQUIRED_FIELDS:
            value = profile.get(field)
            if value is None or value == "":
                return field
        return None

    def get_question(self, field: str) -> str:
        return self.QUESTIONS.get(field, f"Pouvez-vous me donner votre {field} ?")

    def get_suggestions(self, field: str) -> list[str]:
        return self.SUGGESTIONS.get(field, [])


    def infer_region(self, ville: str | None) -> str | None:
        """Déduit la région depuis une ville via un mapping fiable (sinon None)."""
        if not ville:
            return None
        key = ville.strip().casefold()
        if key in self.VILLE_TO_REGION:
            return self.VILLE_TO_REGION[key]
        for v, region in self.VILLE_TO_REGION.items():
            if v in key:
                return region
        return None

    def location_known(self, profile: dict) -> bool:
        return bool(profile.get("ville")) or bool(profile.get("region"))

    def age_known(self, profile: dict) -> bool:
        return profile.get("age") is not None or profile.get("age_refused") is True

    def is_sufficient_for_recommendation(self, profile: dict) -> bool:
        return self.location_known(profile) and self.age_known(profile)

    def missing_blocking_fields(self, profile: dict) -> list[str]:
        missing = []
        if not self.location_known(profile):
            missing.append("ville")
        if not self.age_known(profile):
            missing.append("age")
        return missing

    def next_blocking_field(self, profile: dict) -> str | None:
        for field in self.COLLECT_ORDER:
            if field in self.missing_blocking_fields(profile):
                return field
        return None

    def detects_age_refusal(self, message: str) -> bool:
        return bool(self.REFUSAL_PATTERNS.search(message))


class ConversationBrain:
    def __init__(self) -> None:
        self.intent_detector = IntentDetector()
        self.profile_collector = ProfileCollector()
        self.state_machine = StateMachine()

    def decide(
        self,
        user_message: str,
        conversation_meta: ConversationMeta,
        user_profile: dict,
    ) -> ConversationDecision:
        logger.info("[DECIDE] Analyse du message: %s", user_message[:100])
        logger.info("[DECIDE] État actuel: %s | Profil DB: %s",
                     conversation_meta.state.value,
                     {k: v for k, v in user_profile.items() if v})

        intent = self.intent_detector.detect(user_message, conversation_meta)
        extracted = self.profile_collector.extract(user_message)

        # Si la ville est connue et la région absente, on déduit la région via
        # un mapping fiable uniquement (ne jamais inventer pour une ville inconnue).
        if extracted.get("ville") and not extracted.get("region"):
            inferred = self.profile_collector.infer_region(extracted["ville"])
            if inferred:
                extracted["region"] = inferred

        # Refus explicite de l'âge : mémoriser pour ne pas redemander indéfiniment.
        if self.profile_collector.detects_age_refusal(user_message):
            extracted["age_refused"] = True

        merged = self._merge_profiles(user_profile, conversation_meta.collected_fields, extracted)
        profile_complete = self.profile_collector.is_complete(merged)
        new_state = self.state_machine.next_state(
            conversation_meta.state, intent, profile_complete
        )

        # Champs bloquants réellement manquants (localisation + âge uniquement).
        blocking_missing = self.profile_collector.missing_blocking_fields(merged)
        field_to_ask = self.profile_collector.next_blocking_field(merged)

        social_intent = intent in {
            IntentCategory.GREETING,
            IntentCategory.HOW_ARE_YOU,
            IntentCategory.THANKS,
            IntentCategory.GOODBYE,
            IntentCategory.HELP,
        }
        should_ask_question = bool(blocking_missing) and not social_intent

        logger.info("[DECIDE] Résultat — intent=%s | new_state=%s | "
                     "extracted=%s | profil_complet=%s | bloquants_manquants=%s | field_to_ask=%s",
                     intent.value, new_state.value,
                     extracted, profile_complete, blocking_missing, field_to_ask)

        return ConversationDecision(
            intent=intent,
            new_state=new_state,
            should_ask_question=should_ask_question,
            field_to_ask=field_to_ask,
            extracted_info=extracted,
            merged_profile=merged,
            clarification_needed=False,
        )

    def should_recommend(
        self,
        meta: ConversationMeta,
        merged_profile: dict,
        intent: IntentCategory | None = None,
    ) -> bool:
        """
        Décide si des recommandations doivent être calculées (avant l'appel Dify).
        Basé sur :
        - Le profil est complet (tous les champs requis sont remplis)
        - Les recommandations n'ont pas déjà été montrées
        - Le contexte conversationnel est pertinent (pas une simple salutation/merci)
        """
        if meta.recommendation_shown:
            logger.info("[RECOMMEND_CHECK] Déjà montré — skip")
            return False
        if not self.profile_collector.is_sufficient_for_recommendation(merged_profile):
            logger.info("[RECOMMEND_CHECK] Profil insuffisant — bloquants manquants: %s",
                         self.profile_collector.missing_blocking_fields(merged_profile))
            return False
        # Ne pas recommander si l'intention est purement sociale
        if intent and intent in {
            IntentCategory.GREETING,
            IntentCategory.HOW_ARE_YOU,
            IntentCategory.THANKS,
            IntentCategory.GOODBYE,
            IntentCategory.HELP,
        }:
            logger.info("[RECOMMEND_CHECK] Intention sociale (%s) — pas de recommandation", intent.value)
            return False
        logger.info("[RECOMMEND_CHECK] ✅ Profil complet + intention pertinente (%s) — recommandation autorisée",
                     intent.value if intent else "N/A")
        return True

    def _merge_profiles(
        self, db_profile: dict, collected: dict, extracted: dict
    ) -> dict:
        merged = dict(db_profile)
        merged.update(collected)
        merged.update(extracted)
        return merged