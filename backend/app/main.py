from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes.auth import router as auth_router
from app.routes.admin import router as admin_router
from app.routes.dashboard import router as dashboard_router
from app.routes.home import router as home_router
from app.routes.users import router as users_router
from app.core.config import CORS_ORIGINS, CORS_ORIGIN_REGEX
from fastapi.staticfiles import StaticFiles
import os, threading
from app.scraping.scheduler import start_scheduler
from app.database.database import Base, engine
from app.database.session import SessionLocal
from app.services.admin_service import reactivate_expired_suspensions
from sqlalchemy import text

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_origin_regex=CORS_ORIGIN_REGEX,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(users_router)
app.include_router(home_router)
app.include_router(dashboard_router)
app.include_router(dashboard_router, prefix="/api")
app.include_router(admin_router)
app.include_router(admin_router, prefix="/api")

os.makedirs("uploads/profiles", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
@app.get("/")
def home():
    return {"message": "Bienvenue sur AidFinder"}
@app.on_event("startup")
def startup_event():
    ensure_database_schema()
    threading.Thread(target=start_scheduler, daemon=True).start()
    threading.Thread(target=monitor_expired_suspensions, daemon=True).start()


def ensure_database_schema():
    Base.metadata.create_all(bind=engine)
    ensure_runtime_columns()


def ensure_runtime_columns():
    if engine.dialect.name != "postgresql":
        return
    add_column_statements = (
        "ALTER TABLE aides ADD COLUMN IF NOT EXISTS est_active BOOLEAN NOT NULL DEFAULT TRUE",
        "ALTER TABLE aides ADD COLUMN IF NOT EXISTS source_record_id VARCHAR",
        "ALTER TABLE aides ADD COLUMN IF NOT EXISTS reference_offre VARCHAR",
        "ALTER TABLE aides ADD COLUMN IF NOT EXISTS entreprise_nom VARCHAR",
        "ALTER TABLE aides ADD COLUMN IF NOT EXISTS date_publication DATE",
        "ALTER TABLE aides ADD COLUMN IF NOT EXISTS lieu_travail VARCHAR",
        "CREATE UNIQUE INDEX IF NOT EXISTS ix_aides_source_record_id ON aides (source_id, source_record_id) WHERE source_record_id IS NOT NULL",
        "CREATE INDEX IF NOT EXISTS ix_aides_content_hash ON aides (content_hash)",
        "ALTER TABLE scraping_logs ALTER COLUMN finished_at DROP NOT NULL",
        "ALTER TABLE scraping_logs ALTER COLUMN duration DROP NOT NULL",
        "ALTER TABLE utilisateurs ADD COLUMN IF NOT EXISTS ville VARCHAR",
        "ALTER TABLE utilisateurs ADD COLUMN IF NOT EXISTS date_derniere_connexion TIMESTAMP NULL",
        "ALTER TABLE utilisateurs ADD COLUMN IF NOT EXISTS theme VARCHAR NOT NULL DEFAULT 'light'",
        "ALTER TABLE utilisateurs ADD COLUMN IF NOT EXISTS nombre_avertissements INTEGER NOT NULL DEFAULT 0",
        "ALTER TABLE utilisateurs ADD COLUMN IF NOT EXISTS date_fin_suspension TIMESTAMPTZ NULL",
        "ALTER TABLE historiques ADD COLUMN IF NOT EXISTS conversation_meta TEXT",
        "ALTER TABLE actions_moderations ADD COLUMN IF NOT EXISTS message_conversation TEXT",
        "UPDATE utilisateurs SET statut_compte = 'actif' WHERE statut_compte IN ('desactive', 'desactive_utilisateur')",
        """
        UPDATE utilisateurs
        SET statut_compte = 'suspendu',
            date_fin_suspension = COALESCE(date_fin_suspension, date_desactivation + INTERVAL '15 days', NOW())
        WHERE statut_compte = 'suspendu_admin'
        """,
        "ALTER TABLE utilisateurs ALTER COLUMN statut_compte SET DEFAULT 'actif'",
        "UPDATE utilisateurs u SET statut_compte = 'actif', nombre_avertissements = 0, date_fin_suspension = NULL WHERE u.statut_compte = 'suspendu' AND u.nombre_avertissements = 0 AND NOT EXISTS (SELECT 1 FROM actions_moderations am WHERE am.user_id = u.user_id)",
    )
    utc_datetime_columns = (
        ("utilisateurs", "date_creation"),
        ("utilisateurs", "date_derniere_connexion"),
        ("utilisateurs", "date_desactivation"),
        ("utilisateurs", "date_fin_suspension"),
        ("historiques", "date_creation"),
        ("historiques", "date_derniere_activite"),
        ("discussions", "date_creation"),
        ("aides", "date_creation"),
        ("aides", "derniere_mise_a_jour"),
        ("consultations_aides", "date_consultation"),
        ("exports_pdf", "date_creation"),
        ("notifications", "date_creation"),
        ("resultats_chatbots", "date_creation"),
        ("actions_moderations", "date_creation"),
        ("scraping_logs", "started_at"),
        ("scraping_logs", "finished_at"),
        ("scraping_logs", "created_at"),
        ("sources_aides", "derniere_collecte"),
    )
    with engine.begin() as connection:
        for statement in add_column_statements:
            connection.execute(text(statement))
        for table_name, column_name in utc_datetime_columns:
            data_type = connection.execute(
                text(
                    """
                    SELECT data_type
                    FROM information_schema.columns
                    WHERE table_schema = current_schema()
                      AND table_name = :table_name
                      AND column_name = :column_name
                    """
                ),
                {"table_name": table_name, "column_name": column_name},
            ).scalar()
            if data_type and data_type != "timestamp with time zone":
                connection.execute(
                    text(
                        f"ALTER TABLE {table_name} ALTER COLUMN {column_name} "
                        f"TYPE TIMESTAMPTZ USING {column_name} AT TIME ZONE 'UTC'"
                    )
                )


def monitor_expired_suspensions():
    while True:
        db = SessionLocal()
        try:
            reactivate_expired_suspensions(db)
        finally:
            db.close()
        threading.Event().wait(1)
