from typing import Literal, Protocol

from pydantic import BaseModel, Field

DETAILS_CODES = (
    "content_too_sensitive",
    "unclear_request",
    "language_not_supported",
    "requires_factual_info",
    "personal_attack",
    "legal_threat",
    "competitor_mention",
    "incoherent_review",
    "off_topic",
    "spam_or_fake",
    "extreme_negative",
    "request_for_contact",
    "generation_error",
)
DetailsCode = Literal[
    "content_too_sensitive",
    "unclear_request",
    "language_not_supported",
    "requires_factual_info",
    "personal_attack",
    "legal_threat",
    "competitor_mention",
    "incoherent_review",
    "off_topic",
    "spam_or_fake",
    "extreme_negative",
    "request_for_contact",
    "generation_error",
    "",
]


class LLMResponse(BaseModel):
    """Strict-validated payload coming back from the LLM tool-use call."""

    status: Literal[0, 1] = Field(description="0 = refusal, 1 = success")
    content: str
    details: DetailsCode = ""
    tokens_input: int = 0
    tokens_output: int = 0
    model: str


class LLMRequest(BaseModel):
    system_prompt: str
    user_prompt: str
    model: str
    temperature: float = 0.7
    max_tokens: int = 600


class LLMProvider(Protocol):
    async def generate(self, request: LLMRequest) -> LLMResponse: ...
