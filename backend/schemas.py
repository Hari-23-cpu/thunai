from pydantic import BaseModel, Field
from typing import Any

class ChatRequest(BaseModel):
    conversation_id: str = Field(min_length=1)
    message: str = Field(min_length=1)

class IntentResult(BaseModel):
    intent: str
    confidence: float
    reason: str

class ReplyResult(BaseModel):
    reply: str
    evidence: list[str]
    evidence_sufficient: bool
    reason: str

class EscalationResult(BaseModel):
    decision: str
    reason: str
    confidence: float

class HistoricalMatch(BaseModel):
    tweet_id: str
    thread_id: Any
    customer_message: str
    historical_response: str
    similarity: float

class ChatResponse(BaseModel):
    conversation_id: str
    customer_message: str
    intent: IntentResult
    historical_matches: list[HistoricalMatch]
    reply: ReplyResult
    escalation: EscalationResult