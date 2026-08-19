from sqlalchemy.orm import Session

from app.core.datetime_utils import utc_now
from app.models.aides import Aides
from app.models.categorie_aide import CategorieAide
from app.models.source_aide import SourceAide
from app.database.database import SessionLocal

DEFAULT_IMAGE_URL = "https://anapec.ma/assets/img/logo.png"

SYNC_COMPARE_FIELDS = (
    "source_id",
    "categorie_id",
    "titre",
    "description",
    "date_limite",
    "type_aide",
    "montant",
    "age_min",
    "age_max",
    "region_cible",
    "niveau_etude_requis",
    "statut_socio_pro_requis",
    "handicap_requis",
    "content_hash",
    "url_officielle",
    "image_url",
    "source_record_id",
    "reference_offre",
    "entreprise_nom",
    "date_publication",
    "lieu_travail",
)


def _empty_stats() -> dict:
    return {
        "records": 0,
        "new_records": 0,
        "updated_records": 0,
        "unchanged_records": 0,
        "duplicate_records": 0,
        "expired_records": 0,
        "errors": 0,
    }


def get_or_create_source(db: Session, data: dict) -> SourceAide:
    "Retourne une source existante ou la crée."
    source_url = data.get("source_url") or data.get("url_officielle")
    source_nom = data.get("source_nom") or "Source inconnue"

    source = None
    if source_url:
        source = db.query(SourceAide).filter(SourceAide.url == source_url).first()
    if source is None:
        source = db.query(SourceAide).filter(SourceAide.nom == source_nom).first()

    now = utc_now()
    if source is None:
        source = SourceAide(
            nom=source_nom,
            url=source_url,
            type_source=data.get("source_type"),
            est_fiable=data.get("source_fiable", True),
            derniere_collecte=now,
        )
        db.add(source)
        db.flush()
    else:
        source.derniere_collecte = now
        if data.get("source_type"):
            source.type_source = data["source_type"]
        source.est_fiable = data.get("source_fiable", source.est_fiable)

    return source


def get_or_create_category(db: Session, data: dict) -> CategorieAide:
    "Retourne une catégorie existante ou la crée."
    category_name = data.get("categorie_nom") or data.get("type_aide") or "Autres aides"
    category = db.query(CategorieAide).filter(CategorieAide.nom == category_name).first()
    if category is None:
        category = CategorieAide(
            nom=category_name,
            description=data.get("categorie_description"),
        )
        db.add(category)
        db.flush()
    elif data.get("categorie_description") and not category.description:
        category.description = data["categorie_description"]

    return category


def prepare_aide_data(
    data: dict,
    source: SourceAide,
    category: CategorieAide,
) -> dict | None:
    "Valide et enrichit une aide avant insertion."
    if not data.get("content_hash") or not data.get("titre") or not data.get("url_officielle"):
        return None

    data["image_url"] = data.get("image_url") or DEFAULT_IMAGE_URL

    allowed_fields = {column.name for column in Aides.__table__.columns}
    aide_data = {key: value for key, value in data.items() if key in allowed_fields}
    aide_data["source_id"] = source.source_id
    aide_data["categorie_id"] = category.categorie_id

    return aide_data


def _record_key(data: dict) -> str | None:
    return data.get("source_record_id") or data.get("content_hash")


def _has_changes(aide: Aides, data: dict) -> bool:
    if aide.est_active is not True:
        return True
    return any(getattr(aide, field, None) != data.get(field) for field in SYNC_COMPARE_FIELDS)


def _apply_update(aide: Aides, data: dict) -> None:
    for field in SYNC_COMPARE_FIELDS:
        setattr(aide, field, data.get(field))
    aide.est_active = True
    aide.derniere_mise_a_jour = utc_now()


def save_records(records: list, deactivate_missing: bool = False) -> dict:
    "Synchronise une liste d'aides et retourne des statistiques fiables."
    stats = _empty_stats()
    stats["records"] = len(records or [])
    if not records:
        return stats

    db = SessionLocal()
    try:
        first_record = records[0]
        source = get_or_create_source(db, first_record)
        category = get_or_create_category(db, first_record)

        prepared_by_key = {}
        for record in records:
            try:
                prepared = prepare_aide_data(record, source, category)
                key = _record_key(prepared or {})
                if not prepared or not key:
                    stats["errors"] += 1
                    continue
                if key in prepared_by_key:
                    stats["duplicate_records"] += 1
                prepared_by_key[key] = prepared
            except Exception:
                stats["errors"] += 1

        source_record_ids = [
            data["source_record_id"]
            for data in prepared_by_key.values()
            if data.get("source_record_id")
        ]
        content_hashes = [
            data["content_hash"]
            for data in prepared_by_key.values()
            if data.get("content_hash")
        ]

        existing_by_source_record_id = {}
        if source_record_ids:
            rows = (
                db.query(Aides)
                .filter(
                    Aides.source_id == source.source_id,
                    Aides.source_record_id.in_(source_record_ids),
                )
                .all()
            )
            existing_by_source_record_id = {row.source_record_id: row for row in rows}

        existing_by_hash = {}
        if content_hashes:
            rows = (
                db.query(Aides)
                .filter(
                    Aides.source_id == source.source_id,
                    Aides.content_hash.in_(content_hashes),
                )
                .all()
            )
            existing_by_hash = {row.content_hash: row for row in rows}

        for data in prepared_by_key.values():
            existing = None
            if data.get("source_record_id"):
                existing = existing_by_source_record_id.get(data["source_record_id"])
            if existing is None:
                existing = existing_by_hash.get(data["content_hash"])

            if existing is None:
                db.add(Aides(**data, est_active=True, derniere_mise_a_jour=utc_now()))
                stats["new_records"] += 1
            elif _has_changes(existing, data):
                _apply_update(existing, data)
                stats["updated_records"] += 1
            else:
                stats["unchanged_records"] += 1

        if deactivate_missing and source_record_ids:
            stats["expired_records"] = (
                db.query(Aides)
                .filter(
                    Aides.source_id == source.source_id,
                    Aides.categorie_id == category.categorie_id,
                    Aides.source_record_id.isnot(None),
                    Aides.source_record_id.notin_(source_record_ids),
                    Aides.est_active.is_(True),
                )
                .update(
                    {
                        "est_active": False,
                        "derniere_mise_a_jour": utc_now(),
                    },
                    synchronize_session=False,
                )
            )

        db.commit()
        return stats
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
