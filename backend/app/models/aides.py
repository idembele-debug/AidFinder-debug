from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean, Text, Date, Float
from sqlalchemy.orm import relationship
from app.database.database import Base
from app.core.datetime_utils import utc_now

class Aides(Base):
    __tablename__="aides"
    aide_id = Column(Integer, primary_key=True, index=True)
    source_id = Column(Integer, ForeignKey("sources_aides.source_id"))
    categorie_id = Column(Integer, ForeignKey("categories_aides.categorie_id"))
    titre = Column(String, nullable=False)
    description = Column(Text)
    date_limite = Column(Date)
    type_aide = Column(String)
    montant = Column(Float)
    age_min= Column(Integer)
    age_max= Column(Integer)
    region_cible = Column(String)
    niveau_etude_requis = Column(String)
    statut_socio_pro_requis = Column(String)
    handicap_requis = Column(Boolean)
    content_hash = Column(String)
    source_record_id = Column(String, index=True)
    reference_offre = Column(String)
    entreprise_nom = Column(String)
    date_publication = Column(Date)
    lieu_travail = Column(String)
    date_creation = Column(DateTime(timezone=True), default=utc_now)
    derniere_mise_a_jour = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)
    url_officielle = Column(String)
    image_url = Column(String)
    est_active = Column(Boolean, default=True, nullable=False)
    
    #les relations avec les autres tables
    resultats_chatbots = relationship("ResultatChatbot", back_populates="aide")
    consultations = relationship("ConsultationAide", back_populates="aide", cascade="all, delete-orphan")
    documents_requis = relationship("DocumentRequis", back_populates="aide", cascade="all, delete-orphan")
    categorie = relationship("CategorieAide", back_populates="aides")
    source = relationship("SourceAide", back_populates="aides")
