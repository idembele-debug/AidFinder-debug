from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, EmailStr, field_serializer

from app.core.datetime_utils import as_utc


class AdminDashboardStatsResponse(BaseModel):
    total_utilisateurs: int
    total_aides: int
    total_categories: int
    total_sources: int
    total_conversations: int
    total_pdf_exportes: int
    comptes_actifs: int
    comptes_desactives: int


class AdminUserResponse(BaseModel):
    user_id: int
    nom: str
    email: EmailStr
    role: str
    statut_compte: str
    nombre_avertissements: int
    date_naissance: date | None = None
    ville: str | None = None
    region: str | None = None
    niveau_etude: str | None = None
    statut_socio_pro: str | None = None
    situation_handicap: bool | None = None
    photo_profil: str | None = None
    date_creation: datetime | None = None
    date_derniere_connexion: datetime | None = None
    date_desactivation: datetime | None = None
    date_fin_suspension: datetime | None = None

    model_config = ConfigDict(from_attributes=True)

    @field_serializer("date_creation", "date_derniere_connexion", "date_desactivation", "date_fin_suspension")
    def serialize_datetime(self, value: datetime | None):
        return as_utc(value)


class AdminWarningCreate(BaseModel):
    motif: str
    discussion_id: int


class AdminWarningResponse(BaseModel):
    action_id: int
    motif: str
    message_conversation: str | None = None
    date_creation: datetime
    nombre_avertissements: int
    suspension_declenchee: bool

    @field_serializer("date_creation")
    def serialize_datetime(self, value: datetime):
        return as_utc(value)


class AdminAideBase(BaseModel):
    source_id: int
    categorie_id: int
    titre: str
    description: str | None = None
    date_limite: date | None = None
    type_aide: str | None = None
    montant: float | None = None
    age_min: int | None = None
    age_max: int | None = None
    region_cible: str | None = None
    niveau_etude_requis: str | None = None
    statut_socio_pro_requis: str | None = None
    handicap_requis: bool | None = None
    url_officielle: str | None = None
    image_url: str | None = None
    est_active: bool = True


class AdminAideCreate(AdminAideBase):
    pass


class AdminAideResponse(AdminAideBase):
    aide_id: int
    source_id: int | None = None
    categorie_id: int | None = None
    categorie: str | None = None
    source: str | None = None
    date_creation: datetime | None = None
    derniere_mise_a_jour: datetime | None = None

    @field_serializer("date_creation", "derniere_mise_a_jour")
    def serialize_datetime(self, value: datetime | None):
        return as_utc(value)


class AdminSourceResponse(BaseModel):
    source_id: int
    nom: str
    url: str | None = None
    type_source: str | None = None
    est_fiable: bool
    fiabilite: str
    nombre_aides: int
    dernier_scraping: datetime | None = None
    statut: str

    @field_serializer("dernier_scraping")
    def serialize_datetime(self, value: datetime | None):
        return as_utc(value)


class AdminSourceScrapeResponse(BaseModel):
    message: str
    source_id: int
    source: str
    records: int
    new_records: int = 0
    updated_records: int = 0
    unchanged_records: int = 0
    duplicate_records: int = 0
    expired_records: int = 0
    errors: int = 0
    duration_seconds: float = 0.0
    dernier_scraping: datetime | None = None

    @field_serializer("dernier_scraping")
    def serialize_datetime(self, value: datetime | None):
        return as_utc(value)


class StatItem(BaseModel):
    label: str
    total: int


class EvolutionItem(BaseModel):
    date: date
    total: int


class AdminStatsResponse(BaseModel):
    aides_par_categorie: list[StatItem]
    aides_par_region: list[StatItem]
    evolution_utilisateurs: list[EvolutionItem]
    evolution_conversations: list[EvolutionItem]
    evolution_exports_pdf: list[EvolutionItem]
    sources_les_plus_utilisees: list[StatItem]


class AdminScrapeLogResponse(BaseModel):
    scraplogs_id: int
    source: str
    started_at: datetime
    finished_at: datetime | None = None
    duration: str | None = None
    new_records: int
    updated_records: int
    expired_records: int
    status: str
    error_message: str | None = None
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)

    @field_serializer("started_at", "finished_at", "created_at")
    def serialize_datetime(self, value: datetime | None):
        return as_utc(value)


class AdminConnectionLogResponse(BaseModel):
    user_id: int
    nom: str
    email: EmailStr
    role: str
    date_derniere_connexion: datetime | None = None

    @field_serializer("date_derniere_connexion")
    def serialize_datetime(self, value: datetime | None):
        return as_utc(value)


class AdminLogsResponse(BaseModel):
    derniers_scrapes: list[AdminScrapeLogResponse]
    dernieres_erreurs: list[AdminScrapeLogResponse]
    dernieres_connexions: list[AdminConnectionLogResponse]


class MessageResponse(BaseModel):
    message: str
