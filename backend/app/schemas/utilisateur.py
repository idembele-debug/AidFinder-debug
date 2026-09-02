from datetime import datetime, date
from typing import Literal
from pydantic import BaseModel, EmailStr, ConfigDict, field_serializer

from app.core.datetime_utils import as_utc

class UserCreate(BaseModel):
    
    nom: str
    email: EmailStr
    password: str
    
class UserLogin(BaseModel):
    
    email: EmailStr
    password: str

class MessageResponse(BaseModel):
    message: str
    
class UploadPhotoResponse(BaseModel):
    message: str
    photo_profil: str


class ThemeResponse(BaseModel):
    theme: Literal["light", "dark"]


class ThemeUpdate(BaseModel):
    theme: Literal["light", "dark"]

class UserProfileUpdate(BaseModel):
    # `extra="forbid"` : tout champ inconnu est rejeté explicitement (HTTP 422)
    # au lieu d'être ignoré silencieusement.
    model_config = ConfigDict(extra="forbid")

    nom: str | None = None
    date_naissance: date | None = None
    ville: str | None = None
    region: str | None = None
    niveau_etude: str | None = None
    statut_socio_pro: str | None = None
    situation_handicap: bool | None = None
    photo_profil: str | None = None

class UserProfileResponse(BaseModel):
    user_id: int
    nom: str
    email: EmailStr
    role: str
    statut_compte: str
    
    date_naissance: date | None = None
    ville: str | None = None
    region: str | None = None
    niveau_etude: str | None = None
    statut_socio_pro: str | None = None
    situation_handicap: bool | None = None
    photo_profil: str | None = None
    date_creation: datetime
    model_config = ConfigDict(from_attributes=True)

    @field_serializer("date_creation")
    def serialize_datetime(self, value: datetime | None):
        return as_utc(value)

class ChangePassword(BaseModel):
    current_password: str
    new_password: str
    confirm_new_password: str
    
class UserResponse(BaseModel):
    user_id: int
    nom: str
    email: EmailStr
    role: str
    statut_compte: str
    date_naissance: date | None=None
    ville: str | None = None
    date_creation: datetime
    model_config = ConfigDict(from_attributes=True)

    @field_serializer("date_creation")
    def serialize_datetime(self, value: datetime | None):
        return as_utc(value)
    
class Token(BaseModel):
    access_token: str
    token_type: str
    
