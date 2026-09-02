from datetime import datetime

from pydantic import BaseModel, Field, field_serializer

from app.core.datetime_utils import as_utc
from app.schemas.dashboard import DashboardAidResponse
from app.services.conversation_engine import ConversationState


class ChatMessageRequest(BaseModel):
    historique_id: int | None = None
    message: str = Field(..., min_length=1)


class ChatDiscussionMessage(BaseModel):
    discussion_id: int
    expediteur: str
    contenu: str
    date_creation: datetime | None = None

    @field_serializer("date_creation")
    def serialize_datetime(self, value: datetime | None):
        return as_utc(value)


class ChatMessageResponse(BaseModel):
    historique_id: int
    titre_resume: str
    date_derniere_activite: datetime | None = None
    user_message: ChatDiscussionMessage
    bot_message: ChatDiscussionMessage
    aides_recommandees: list[DashboardAidResponse] = Field(default_factory=list)
    conversation_state: ConversationState = ConversationState.GREETING
    champs_manquants: list[str] = Field(default_factory=list)
    question_actuelle: str | None = None
    suggestions: list[str] = Field(default_factory=list)

    @field_serializer("date_derniere_activite")
    def serialize_datetime(self, value: datetime | None):
        return as_utc(value)


# ── Streaming SSE schemas ─────────────────────────────────────────────

class ChatStreamMessageRequest(BaseModel):
    """Same as ChatMessageRequest, but used for the streaming endpoint."""
    historique_id: int | None = None
    message: str = Field(..., min_length=1)