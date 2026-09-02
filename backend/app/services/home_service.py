from sqlalchemy import case, desc, func, or_
from sqlalchemy.orm import Session

from app.models.aides import Aides
from app.models.categorie_aide import CategorieAide
from app.models.discussion import Discussion
from app.models.source_aide import SourceAide
from app.models.utilisateurs import Utilisateur

DESCRIPTION_LIMIT = 150


def _truncate_description(description: str | None, limit: int = DESCRIPTION_LIMIT) -> str | None:
    """Prépare un résumé court pour les cartes de la page d'accueil."""
    if description is None or len(description) <= limit:
        return description
    return f"{description[:limit].rstrip()}..."


def _serialize_aide(aide: Aides) -> dict:
    return {
        "aide_id": aide.aide_id,
        "titre": aide.titre,
        "description": _truncate_description(aide.description),
        "image_url": aide.image_url,
        "region_cible": aide.region_cible,
        "type_aide": aide.type_aide,
        "url_officielle": aide.url_officielle,
        "date_creation": aide.date_creation,
    }


def get_latest_aids(db: Session, limit: int = 6) -> list[dict]:
    """Retourne les aides actives les plus récentes enregistrées en base."""
    aides = (
        db.query(Aides)
        .filter(Aides.est_active.is_(True))
        .order_by(desc(Aides.date_creation), desc(Aides.aide_id))
        .limit(limit)
        .all()
    )
    return [_serialize_aide(aide) for aide in aides]


def get_home_stats(db: Session) -> dict:
    """Calcule les chiffres publics de la page d'accueil depuis PostgreSQL.

    `total_aides` ne compte QUE les offres/aides actives : le compteur doit
    refléter les données réellement visibles et exploitables, pas l'historique
    des enregistrements scrapés (y compris les offres désactivées).
    """
    total_aides = (
        db.query(func.count(Aides.aide_id))
        .filter(Aides.est_active.is_(True))
        .scalar()
        or 0
    )
    total_categories = db.query(func.count(CategorieAide.categorie_id)).scalar() or 0
    total_sources = db.query(func.count(SourceAide.source_id)).scalar() or 0
    total_utilisateurs = db.query(func.count(Utilisateur.user_id)).scalar() or 0
    total_conversations = db.query(func.count(Discussion.discussion_id)).scalar() or 0
    derniere_mise_a_jour = db.query(func.max(Aides.derniere_mise_a_jour)).scalar()

    return {
        "total_aides": total_aides,
        "total_categories": total_categories,
        "total_sources": total_sources,
        "total_utilisateurs": total_utilisateurs,
        "total_conversations": total_conversations,
        "derniere_mise_a_jour": derniere_mise_a_jour,
    }


def get_home_categories(db: Session) -> list[dict]:
    """Liste les catégories avec le nombre d'aides rattachées à chacune."""
    categories = (
        db.query(
            CategorieAide.categorie_id,
            CategorieAide.nom,
            CategorieAide.description,
            func.count(Aides.aide_id).label("nombre_aides"),
        )
        .outerjoin(Aides, Aides.categorie_id == CategorieAide.categorie_id)
        .group_by(
            CategorieAide.categorie_id,
            CategorieAide.nom,
            CategorieAide.description,
        )
        .order_by(CategorieAide.nom)
        .all()
    )

    return [
        {
            "id": categorie.categorie_id,
            "nom": categorie.nom,
            "description": categorie.description,
            "nombre_aides": categorie.nombre_aides,
        }
        for categorie in categories
    ]


def search_home_aids(db: Session, query: str, limit: int = 20) -> list[dict]:
    """Recherche rapidement dans les titres et descriptions des aides."""
    normalized_query = query.strip()
    if not normalized_query:
        return []

    pattern = f"%{normalized_query}%"
    relevance = case(
        (Aides.titre.ilike(pattern), 2),
        (Aides.description.ilike(pattern), 1),
        else_=0,
    )

    aides = (
        db.query(Aides)
        .filter(Aides.est_active.is_(True))
        .filter(or_(Aides.titre.ilike(pattern), Aides.description.ilike(pattern)))
        .order_by(desc(relevance), desc(Aides.date_creation), desc(Aides.aide_id))
        .limit(limit)
        .all()
    )

    return [_serialize_aide(aide) for aide in aides]
