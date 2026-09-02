import logging
import smtplib
from datetime import timedelta
from email.message import EmailMessage

from fastapi import HTTPException, status
from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app.core.datetime_utils import as_utc, utc_now
from app.core.config import (
    SMTP_FROM_EMAIL,
    SMTP_HOST,
    SMTP_PASSWORD,
    SMTP_PORT,
    SMTP_USERNAME,
    SMTP_USE_TLS,
)
from app.core.statuts_compte import ACTIF, SUSPENDU, est_suspendu
from app.models.action_moderation import ActionModeration
from app.models.aides import Aides
from app.models.categorie_aide import CategorieAide
from app.models.consultation_aide import ConsultationAide
from app.models.discussion import Discussion
from app.models.export_pdf import ExportPDF
from app.models.historique import Historique
from app.models.notification import Notification
from app.models.scraping_logs import ScrapingLog
from app.models.source_aide import SourceAide
from app.models.utilisateurs import Utilisateur
from app.schemas.admin import AdminAideCreate, AdminWarningCreate
from app.scraping.manager import run_all_scrapers


logger = logging.getLogger(__name__)
SUSPENSION_DURATION = timedelta(days=15)


def _get_user_or_404(db: Session, user_id: int) -> Utilisateur:
    user = db.query(Utilisateur).filter(Utilisateur.user_id == user_id).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilisateur introuvable.")
    return user


def _get_aide_or_404(db: Session, aide_id: int) -> Aides:
    aide = db.query(Aides).filter(Aides.aide_id == aide_id).first()
    if aide is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Aide introuvable.")
    return aide


def _get_source_or_404(db: Session, source_id: int) -> SourceAide:
    source = db.query(SourceAide).filter(SourceAide.source_id == source_id).first()
    if source is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source introuvable.")
    return source


def _ensure_relations_exist(db: Session, source_id: int | None, categorie_id: int | None) -> None:
    if source_id is not None:
        exists = db.query(SourceAide.source_id).filter(SourceAide.source_id == source_id).first()
        if exists is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Source inexistante.")
    if categorie_id is not None:
        exists = db.query(CategorieAide.categorie_id).filter(CategorieAide.categorie_id == categorie_id).first()
        if exists is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Catégorie inexistante.")


def _serialize_aide(aide: Aides) -> dict:
    return {
        "aide_id": aide.aide_id,
        "source_id": aide.source_id,
        "categorie_id": aide.categorie_id,
        "titre": aide.titre,
        "description": aide.description,
        "date_limite": aide.date_limite,
        "type_aide": aide.type_aide,
        "montant": aide.montant,
        "age_min": aide.age_min,
        "age_max": aide.age_max,
        "region_cible": aide.region_cible,
        "niveau_etude_requis": aide.niveau_etude_requis,
        "statut_socio_pro_requis": aide.statut_socio_pro_requis,
        "handicap_requis": aide.handicap_requis,
        "url_officielle": aide.url_officielle,
        "image_url": aide.image_url,
        "est_active": aide.est_active,
        "categorie": aide.categorie.nom if aide.categorie else None,
        "source": aide.source.nom if aide.source else None,
        "date_creation": as_utc(aide.date_creation),
        "derniere_mise_a_jour": as_utc(aide.derniere_mise_a_jour),
    }


def get_dashboard_stats(db: Session) -> dict:
    return {
        "total_utilisateurs": db.query(func.count(Utilisateur.user_id)).scalar() or 0,
        # Cohérence avec la page d'accueil : seules les aides actives comptent.
        "total_aides": (
            db.query(func.count(Aides.aide_id))
            .filter(Aides.est_active.is_(True))
            .scalar()
            or 0
        ),
        "total_categories": db.query(func.count(CategorieAide.categorie_id)).scalar() or 0,
        "total_sources": db.query(func.count(SourceAide.source_id)).scalar() or 0,
        "total_conversations": db.query(func.count(Discussion.discussion_id)).scalar() or 0,
        "total_pdf_exportes": db.query(func.count(ExportPDF.export_id)).scalar() or 0,
        "comptes_actifs": db.query(func.count(Utilisateur.user_id)).filter(Utilisateur.statut_compte == ACTIF).scalar() or 0,
        "comptes_desactives": db.query(func.count(Utilisateur.user_id)).filter(Utilisateur.statut_compte != ACTIF).scalar() or 0,
    }


def list_users(db: Session) -> list[Utilisateur]:
    return db.query(Utilisateur).order_by(desc(Utilisateur.date_creation), desc(Utilisateur.user_id)).all()


def get_user(db: Session, user_id: int) -> Utilisateur:
    return _get_user_or_404(db, user_id)


def _send_email(recipient: str, subject: str, body: str) -> None:
    if not SMTP_HOST:
        logger.warning("Email non envoyé : SMTP_HOST n'est pas configuré.")
        return

    message = EmailMessage()
    message["From"] = SMTP_FROM_EMAIL
    message["To"] = recipient
    message["Subject"] = subject
    message.set_content(body)
    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15) as server:
            if SMTP_USE_TLS:
                server.starttls()
            if SMTP_USERNAME and SMTP_PASSWORD:
                server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(message)
    except (OSError, smtplib.SMTPException):
        logger.exception("Échec de l'envoi de l'email de modération à %s.", recipient)


def _send_warning_email(user: Utilisateur, motif: str, message_conversation: str) -> None:
    if user.nombre_avertissements >= 2:
        consequence = "Ce deuxième avertissement entraîne la suspension immédiate de votre compte."
    else:
        consequence = "Un nouvel avertissement entraînera la suspension de votre compte pendant 15 jours."
    _send_email(
        user.email,
        "AidFinder — avertissement",
        f"Bonjour {user.nom},\n\n"
        f"Motif : {motif}\n"
        f"Message concerné : {message_conversation}\n"
        f"Nombre d'avertissements : {user.nombre_avertissements}\n\n"
        "Nous vous rappelons que l'utilisation d'AidFinder doit respecter le règlement de la plateforme.\n"
        f"{consequence}\n",
    )


def _send_suspension_email(user: Utilisateur, motif: str, suspension_date, reactivation_date) -> None:
    _send_email(
        user.email,
        "AidFinder — compte suspendu",
        f"Bonjour {user.nom},\n\n"
        f"Motif : {motif}\n"
        f"Date de suspension : {as_utc(suspension_date).isoformat()}\n"
        "Durée : 15 jours.\n"
        f"Date prévue de réactivation : {as_utc(reactivation_date).isoformat()}\n",
    )


def _send_reactivation_emails(user: Utilisateur, admin_email: str | None) -> None:
    _send_email(
        user.email,
        "AidFinder — compte réactivé",
        f"Bonjour {user.nom},\n\nVotre compte a été réactivé automatiquement à l'issue de sa suspension.",
    )
    if admin_email:
        _send_email(
            admin_email,
            "AidFinder — réactivation automatique d'un compte",
            f"Le compte de {user.nom} ({user.email}) a été réactivé automatiquement à l'issue de sa suspension.",
        )


def _get_admin_id(admin: Utilisateur) -> int:
    if admin.administrateur is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Le compte administrateur n'est pas associé à un profil administrateur.",
        )
    return admin.administrateur.admin_id


def send_warning(
    db: Session,
    admin: Utilisateur,
    user_id: int,
    data: AdminWarningCreate,
) -> tuple[ActionModeration, bool]:
    user = _get_user_or_404(db, user_id)
    if user.role != "utilisateur":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Seuls les utilisateurs peuvent être avertis.")
    if est_suspendu(user.statut_compte):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ce compte est déjà suspendu.")

    discussion = (
        db.query(Discussion)
        .join(Historique, Discussion.historique_id == Historique.historique_id)
        .filter(Discussion.discussion_id == data.discussion_id, Historique.user_id == user.user_id)
        .first()
    )
    if discussion is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message de conversation introuvable pour cet utilisateur.",
        )

    now = utc_now()
    warning = ActionModeration(
        admin_id=_get_admin_id(admin),
        user_id=user.user_id,
        type_action="avertissement",
        motif=data.motif,
        message_affiche=discussion.contenu,
        message_conversation=discussion.contenu,
        date_creation=now,
    )
    user.nombre_avertissements += 1
    suspension_declenchee = user.nombre_avertissements >= 2
    if suspension_declenchee:
        user.statut_compte = SUSPENDU
        user.date_fin_suspension = now + SUSPENSION_DURATION
        db.add(
            ActionModeration(
                admin_id=warning.admin_id,
                user_id=user.user_id,
                type_action="suspension",
                motif=data.motif,
                message_affiche=discussion.contenu,
                message_conversation=discussion.contenu,
                date_creation=now,
            )
        )
    try:
        db.add(warning)
        db.commit()
        db.refresh(warning)
        db.refresh(user)
    except Exception:
        db.rollback()
        raise

    _send_warning_email(user, data.motif, discussion.contenu)
    
    # Créer une notification pour l'utilisateur
    if suspension_declenchee:
        notification_title = "Compte suspendu"
        notification_message = f"Votre compte a été suspendu pour 15 jours suite à un deuxième avertissement. Motif : {data.motif}"
        _send_suspension_email(user, data.motif, now, user.date_fin_suspension)
    else:
        notification_title = "Avertissement reçu"
        notification_message = f"Vous avez reçu un avertissement. Motif : {data.motif}. Un nouvel avertissement entraînera la suspension de votre compte."
    
    user_notification = Notification(
        user_id=user.user_id,
        titre=notification_title,
        message=notification_message,
    )
    db.add(user_notification)
    db.commit()
    
    return warning, suspension_declenchee


def list_warnings(db: Session, user_id: int) -> list[ActionModeration]:
    _get_user_or_404(db, user_id)
    return (
        db.query(ActionModeration)
        .filter(
            ActionModeration.user_id == user_id,
            ActionModeration.type_action == "avertissement",
        )
        .order_by(desc(ActionModeration.date_creation), desc(ActionModeration.action_id))
        .all()
    )


def reactivate_expired_suspension(db: Session, user: Utilisateur) -> bool:
    if (
        not est_suspendu(user.statut_compte)
        or user.date_fin_suspension is None
        or user.date_fin_suspension > utc_now()
    ):
        return False

    last_suspension = (
        db.query(ActionModeration)
        .filter(
            ActionModeration.user_id == user.user_id,
            ActionModeration.type_action == "suspension",
        )
        .order_by(desc(ActionModeration.date_creation), desc(ActionModeration.action_id))
        .first()
    )
    user.statut_compte = ACTIF
    try:
        if last_suspension is not None:
            db.add(
                ActionModeration(
                    admin_id=last_suspension.admin_id,
                    user_id=user.user_id,
                    type_action="reactivation_automatique",
                    motif="Fin automatique de la période de suspension.",
                    date_creation=utc_now(),
                )
            )
        db.commit()
        db.refresh(user)
    except Exception:
        db.rollback()
        raise

    admin_email = None
    if last_suspension and last_suspension.administrateur and last_suspension.administrateur.utilisateur:
        admin_email = last_suspension.administrateur.utilisateur.email
    _send_reactivation_emails(user, admin_email)
    
    # Créer des notifications pour l'utilisateur et l'admin
    user_notification = Notification(
        user_id=user.user_id,
        titre="Compte réactivé",
        message="Votre compte a été réactivé automatiquement à l'issue de sa suspension.",
    )
    db.add(user_notification)
    
    if admin_email:
        # Trouver l'utilisateur admin correspondant
        admin_user = db.query(Utilisateur).filter(Utilisateur.email == admin_email).first()
        if admin_user:
            admin_notification = Notification(
                user_id=admin_user.user_id,
                titre="Réactivation automatique",
                message=f"Le compte de {user.nom} ({user.email}) a été réactivé automatiquement.",
            )
            db.add(admin_notification)
    
    db.commit()
    return True


def reactivate_expired_suspensions(db: Session) -> int:
    suspended_users = (
        db.query(Utilisateur)
        .filter(
            Utilisateur.statut_compte == SUSPENDU,
            Utilisateur.date_fin_suspension.isnot(None),
            Utilisateur.date_fin_suspension <= utc_now(),
        )
        .all()
    )
    return sum(reactivate_expired_suspension(db, user) for user in suspended_users)


def list_aides(db: Session) -> list[dict]:
    aides = db.query(Aides).order_by(desc(Aides.date_creation), desc(Aides.aide_id)).all()
    return [_serialize_aide(aide) for aide in aides]


def create_aide(db: Session, data: AdminAideCreate) -> dict:
    _ensure_relations_exist(db, data.source_id, data.categorie_id)
    try:
        aide = Aides(**data.model_dump(), derniere_mise_a_jour=utc_now())
        db.add(aide)
        db.commit()
        db.refresh(aide)
        return _serialize_aide(aide)
    except Exception:
        db.rollback()
        raise


def delete_aide(db: Session, aide_id: int) -> dict:
    aide = _get_aide_or_404(db, aide_id)
    try:
        db.delete(aide)
        db.commit()
        return {"message": "Aide supprimée avec succès."}
    except Exception:
        db.rollback()
        raise


def set_aide_active(db: Session, aide_id: int, active: bool) -> dict:
    aide = _get_aide_or_404(db, aide_id)
    try:
        aide.est_active = active
        aide.derniere_mise_a_jour = utc_now()
        db.commit()
        db.refresh(aide)
        return _serialize_aide(aide)
    except Exception:
        db.rollback()
        raise


def list_sources(db: Session) -> list[dict]:
    rows = (
        db.query(
            SourceAide,
            func.count(Aides.aide_id).label("nombre_aides"),
            func.max(ScrapingLog.finished_at).label("dernier_scraping"),
        )
        .outerjoin(Aides, Aides.source_id == SourceAide.source_id)
        .outerjoin(ScrapingLog, ScrapingLog.source == SourceAide.nom)
        .group_by(
            SourceAide.source_id,
            SourceAide.nom,
            SourceAide.url,
            SourceAide.type_source,
            SourceAide.est_fiable,
            SourceAide.derniere_collecte,
        )
        .order_by(SourceAide.nom)
        .all()
    )
    results = []
    for source, nombre_aides, dernier_scraping in rows:
        last_log = (
            db.query(ScrapingLog)
            .filter(ScrapingLog.source == source.nom)
            .order_by(desc(ScrapingLog.finished_at), desc(ScrapingLog.scraplogs_id))
            .first()
        )
        results.append(
            {
                "source_id": source.source_id,
                "nom": source.nom,
                "url": source.url,
                "type_source": source.type_source,
                "est_fiable": source.est_fiable,
                "fiabilite": "fiable" if source.est_fiable else "à vérifier",
                "nombre_aides": nombre_aides or 0,
                "dernier_scraping": dernier_scraping or source.derniere_collecte,
                "statut": last_log.status if last_log else "jamais_scrape",
            }
        )
    return results


def rerun_source_scraping(db: Session, source_id: int) -> dict:
    source = _get_source_or_404(db, source_id)
    try:
        stats = run_all_scrapers(("anapec_emploi",))
        already_running = any(
            item.get("status") == "already_running"
            for item in stats.get("scrapers", [])
        )
        if not already_running:
            source.derniere_collecte = utc_now()
            db.commit()
            db.refresh(source)
        return {
            "message": "Scraping déjà en cours." if already_running else "Scraping terminé.",
            "source_id": source.source_id,
            "source": source.nom,
            "records": stats.get("records", 0),
            "new_records": stats.get("new_records", 0),
            "updated_records": stats.get("updated_records", 0),
            "unchanged_records": stats.get("unchanged_records", 0),
            "duplicate_records": stats.get("duplicate_records", 0),
            "expired_records": stats.get("expired_records", 0),
            "errors": stats.get("errors", 0),
            "duration_seconds": round(stats.get("total_seconds", 0.0), 2),
            "dernier_scraping": source.derniere_collecte,
        }
    except Exception:
        db.rollback()
        raise


def get_statistics(db: Session) -> dict:
    aides_par_categorie = [
        {"label": label or "Sans catégorie", "total": total or 0}
        for label, total in (
            db.query(CategorieAide.nom, func.count(Aides.aide_id))
            .outerjoin(Aides, Aides.categorie_id == CategorieAide.categorie_id)
            .filter(Aides.est_active.is_(True))
            .group_by(CategorieAide.nom)
            .order_by(CategorieAide.nom)
            .all()
        )
    ]
    aides_par_region = [
        {"label": label or "Non renseignée", "total": total or 0}
        for label, total in (
            db.query(Aides.region_cible, func.count(Aides.aide_id))
            .filter(Aides.est_active.is_(True))
            .group_by(Aides.region_cible)
            .order_by(desc(func.count(Aides.aide_id)))
            .all()
        )
    ]
    evolution_utilisateurs = [
        {"date": created_date, "total": total or 0}
        for created_date, total in (
            db.query(func.date(Utilisateur.date_creation), func.count(Utilisateur.user_id))
            .filter(Utilisateur.date_creation.isnot(None))
            .group_by(func.date(Utilisateur.date_creation))
            .order_by(func.date(Utilisateur.date_creation))
            .all()
        )
    ]
    evolution_conversations = [
        {"date": created_date, "total": total or 0}
        for created_date, total in (
            db.query(func.date(Discussion.date_creation), func.count(Discussion.discussion_id))
            .filter(Discussion.date_creation.isnot(None))
            .group_by(func.date(Discussion.date_creation))
            .order_by(func.date(Discussion.date_creation))
            .all()
        )
    ]
    evolution_exports_pdf = [
        {"date": created_date, "total": total or 0}
        for created_date, total in (
            db.query(func.date(ExportPDF.date_creation), func.count(ExportPDF.export_id))
            .filter(ExportPDF.date_creation.isnot(None))
            .group_by(func.date(ExportPDF.date_creation))
            .order_by(func.date(ExportPDF.date_creation))
            .all()
        )
    ]
    sources_les_plus_utilisees = [
        {"label": label or "Source inconnue", "total": total or 0}
        for label, total in (
            db.query(SourceAide.nom, func.count(ConsultationAide.id))
            .join(Aides, Aides.source_id == SourceAide.source_id)
            .join(ConsultationAide, ConsultationAide.aide_id == Aides.aide_id)
            .group_by(SourceAide.nom)
            .order_by(desc(func.count(ConsultationAide.id)))
            .limit(10)
            .all()
        )
    ]
    return {
        "aides_par_categorie": aides_par_categorie,
        "aides_par_region": aides_par_region,
        "evolution_utilisateurs": evolution_utilisateurs,
        "evolution_conversations": evolution_conversations,
        "evolution_exports_pdf": evolution_exports_pdf,
        "sources_les_plus_utilisees": sources_les_plus_utilisees,
    }


def get_logs(db: Session) -> dict:
    derniers_scrapes = db.query(ScrapingLog).order_by(desc(ScrapingLog.created_at), desc(ScrapingLog.scraplogs_id)).limit(10).all()
    dernieres_erreurs = (
        db.query(ScrapingLog)
        .filter(ScrapingLog.error_message.isnot(None))
        .order_by(desc(ScrapingLog.created_at), desc(ScrapingLog.scraplogs_id))
        .limit(10)
        .all()
    )
    users = (
        db.query(Utilisateur)
        .filter(Utilisateur.date_derniere_connexion.isnot(None))
        .order_by(desc(Utilisateur.date_derniere_connexion), desc(Utilisateur.user_id))
        .limit(10)
        .all()
    )
    return {
        "derniers_scrapes": derniers_scrapes,
        "dernieres_erreurs": dernieres_erreurs,
        "dernieres_connexions": [
            {
                "user_id": user.user_id,
                "nom": user.nom,
                "email": user.email,
                "role": user.role,
                "date_derniere_connexion": as_utc(user.date_derniere_connexion),
            }
            for user in users
        ],
    }
