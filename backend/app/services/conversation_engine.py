import json
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any


class ConversationState(str, Enum):
    GREETING = "GREETING"
    COLLECTING_INFO = "COLLECTING_INFO"
    DISCUSSING = "DISCUSSING"
    CLARIFYING = "CLARIFYING"


class IntentCategory(str, Enum):
    GREETING = "GREETING"
    HOW_ARE_YOU = "HOW_ARE_YOU"
    SEARCH_JOB = "SEARCH_JOB"
    SEARCH_STUDY = "SEARCH_STUDY"
    SEARCH_HOUSING = "SEARCH_HOUSING"
    SEARCH_HEALTH = "SEARCH_HEALTH"
    SEARCH_BUSINESS = "SEARCH_BUSINESS"
    ASK_PROFILE = "ASK_PROFILE"
    PROVIDE_INFO = "PROVIDE_INFO"
    ASK_BEST = "ASK_BEST"
    ASK_DETAILS = "ASK_DETAILS"
    ASK_SPECIFIC_AID = "ASK_SPECIFIC_AID"
    THANKS = "THANKS"
    GOODBYE = "GOODBYE"
    HELP = "HELP"
    UNKNOWN = "UNKNOWN"


@dataclass
class ConversationMeta:
    state: ConversationState = ConversationState.GREETING
    previous_state: ConversationState | None = None
    collected_fields: dict[str, Any] = field(default_factory=dict)
    discovered_context: dict[str, Any] = field(default_factory=dict)
    pending_questions: list[str] = field(default_factory=list)
    current_question_index: int = 0
    recommendation_shown: bool = False
    last_recommended_aids: list[int] = field(default_factory=list)
    subject: str | None = None
    dify_conversation_id: str | None = None

    def to_json(self) -> str:
        return json.dumps(asdict(self), default=str)

    @classmethod
    def from_json(cls, data: str | None) -> "ConversationMeta":
        if not data:
            return cls()
        try:
            result = json.loads(data)
            if "state" in result:
                result["state"] = ConversationState(result["state"])
            if "previous_state" in result and result["previous_state"]:
                result["previous_state"] = ConversationState(result["previous_state"])
            return cls(**result)
        except (json.JSONDecodeError, TypeError, ValueError):
            return cls()


@dataclass
class ConversationDecision:
    intent: IntentCategory
    new_state: ConversationState
    should_ask_question: bool
    field_to_ask: str | None
    extracted_info: dict
    merged_profile: dict
    clarification_needed: bool


class StateMachine:
    GREETING_INTENTS = {
        IntentCategory.GREETING,
        IntentCategory.HOW_ARE_YOU,
        IntentCategory.HELP,
    }
    REQUEST_INTENTS = {
        IntentCategory.SEARCH_JOB,
        IntentCategory.SEARCH_STUDY,
        IntentCategory.SEARCH_HOUSING,
        IntentCategory.SEARCH_HEALTH,
        IntentCategory.SEARCH_BUSINESS,
        IntentCategory.ASK_BEST,
        IntentCategory.ASK_DETAILS,
        IntentCategory.ASK_SPECIFIC_AID,
        IntentCategory.PROVIDE_INFO,
    }

    def next_state(
        self,
        current: ConversationState,
        intent: IntentCategory,
        profile_complete: bool,
    ) -> ConversationState:
        """
        The state machine ONLY tracks conversation context.
        It does NOT decide what the bot should say.
        Transitions are purely informational for the LLM.
        """
        if current == ConversationState.GREETING:
            if intent in self.GREETING_INTENTS:
                return ConversationState.GREETING
            if intent in self.REQUEST_INTENTS:
                return ConversationState.DISCUSSING
            return ConversationState.GREETING

        if current == ConversationState.COLLECTING_INFO:
            if profile_complete:
                return ConversationState.DISCUSSING
            return ConversationState.COLLECTING_INFO

        if current == ConversationState.DISCUSSING:
            if intent in self.REQUEST_INTENTS:
                return ConversationState.DISCUSSING
            return ConversationState.DISCUSSING

        if current == ConversationState.CLARIFYING:
            return ConversationState.DISCUSSING

        return current