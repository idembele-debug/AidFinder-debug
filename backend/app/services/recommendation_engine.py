from datetime import date, datetime, timezone
from typing import Any

from sqlalchemy import desc
from sqlalchemy.orm import Session, joinedload

from app.core.datetime_utils import as_utc
from app.models.aides import Aides


class RecommendationEngine:
    PROFILE_FIELDS = [
        "ville", "region", "niveau_etude",
        "statut_socio_pro", "age", "handicap",
    ]

    def calculate_score(self, profile: dict[str, Any], aide: Aides) -> tuple[int, list[str]]:
        score = 0
        raisons: list[str] = []

        region_score, region_reason = self._score_region(
            profile.get("ville"), profile.get("region"), aide.region_cible
        )
        score += region_score
        raisons.append(region_reason)

        study_score, study_reason = self._score_field(
            profile.get("niveau_etude"), aide.niveau_etude_requis,
            "Niveau d'étude", "niveau_etude_requis",
        )
        score += study_score
        raisons.append(study_reason)

        status_score, status_reason = self._score_field(
            profile.get("statut_socio_pro"), aide.statut_socio_pro_requis,
            "Statut", "statut_socio_pro_requis",
        )
        score += status_score
        raisons.append(status_reason)

        age_score, age_reason = self._score_age(
            profile.get("age"), aide.age_min, aide.age_max
        )
        score += age_score
        raisons.append(age_reason)

        handicap_score, handicap_reason = self._score_handicap(
            profile.get("handicap"), aide.handicap_requis
        )
        score += handicap_score
        raisons.append(handicap_reason)

        return min(100, max(0, score)), raisons

    def get_recommendations(
        self,
        db: Session,
        profile: dict[str, Any],
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        aides = (
            db.query(Aides)
            .options(joinedload(Aides.categorie), joinedload(Aides.source))
            .filter(Aides.est_active.is_(True))
            .order_by(desc(Aides.date_creation), desc(Aides.aide_id))
            .all()
        )
        scored = [
            (aide, score, raisons)
            for aide in aides
            for score, raisons in [self.calculate_score(profile, aide)]
        ]
        scored.sort(key=lambda x: (x[1], x[0].aide_id), reverse=True)
        return self._serialize_aids(scored[:limit])

    def _serialize_aids(
        self, scored: list[tuple[Aides, int, list[str]]]
    ) -> list[dict[str, Any]]:
        return [
            {
                "aide_id": aide.aide_id,
                "titre": aide.titre,
                "description": aide.description,
                "categorie": aide.categorie.nom if aide.categorie else aide.type_aide,
                "source": aide.source.nom if aide.source else None,
                "source_url": aide.source.url if aide.source else None,
                # Clé canonique attendue par le frontend + alias rétro-compatible
                # (response_generator consomme encore "lien_officiel").
                "url_officielle": aide.url_officielle,
                "lien_officiel": aide.url_officielle,
                "region_cible": aide.region_cible,
                "niveau_etude_requis": aide.niveau_etude_requis,
                "statut_socio_pro_requis": aide.statut_socio_pro_requis,
                "age_min": aide.age_min,
                "age_max": aide.age_max,
                "handicap_requis": aide.handicap_requis,
                "score_matching": score,
                "raisons": raisons[:5],
            }
            for aide, score, raisons in scored
        ]

    def _is_open(self, value: str | None) -> bool:
        if not value:
            return True
        v = value.strip().casefold()
        return any(t in v for t in ("tous", "toutes", "maroc", "national", "non restrictif"))

    def _normalize(self, value: str | None) -> str:
        return (value or "").strip().casefold()

    def _score_region(
        self, ville: str | None, region: str | None, cible: str | None
    ) -> tuple[int, str]:
        if self._is_open(cible):
            return 25, "Région non restrictive"
        nc = cible.strip().casefold()
        for v in [ville, region]:
            if v and self._normalize(v) in nc:
                return 25, "Région compatible"
        return 0, "Région non compatible"

    def _score_field(
        self, profile_value: str | None, requirement: str | None,
        label: str, _field_name: str,
    ) -> tuple[int, str]:
        if self._is_open(requirement):
            return 20, f"{label} non restrictif"
        if profile_value and self._normalize(profile_value) in self._normalize(requirement):
            return 20, f"{label} compatible"
        return 0, f"{label} non compatible"

    def _score_age(
        self, age: int | None, age_min: int | None, age_max: int | None
    ) -> tuple[int, str]:
        if age_min is None and age_max is None:
            return 20, "Âge non limité"
        if age is None:
            return 0, "Âge non renseigné"
        if (age_min is None or age >= age_min) and (age_max is None or age <= age_max):
            return 20, "Âge compatible"
        return 0, "Âge non compatible"

    def _score_handicap(
        self, handicap: bool | None, handicap_requis: bool | None
    ) -> tuple[int, str]:
        if handicap_requis is True:
            if handicap is True:
                return 15, "Handicap compatible"
            return 0, "Handicap requis"
        return 15, "Handicap non requis"


recommendation_engine = RecommendationEngine()