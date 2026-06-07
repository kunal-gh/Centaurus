"""
Request and response models for API validation.
All endpoints use these schemas.
Spec Reference: Section 6.3
"""
from pydantic import BaseModel, Field
from typing import Optional, Literal


class ChatRequest(BaseModel):
    """Incoming chat query from any supported channel."""
    channel: Literal["web", "email", "whatsapp", "instagram"] = Field(default="web")
    message: str = Field(..., min_length=1)
    user_email: Optional[str] = None
    user_phone: Optional[str] = None
    user_name: Optional[str] = None
    user_instagram: Optional[str] = None


class ChatResponse(BaseModel):
    """Final response returned to caller, including metadata for confidence visualization."""
    response: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    intent: Optional[str] = None
    escalated: bool = False
    reason: Optional[str] = None
    author_found: bool = False
    books_found: int = 0
    sources: Optional[list[dict]] = None



class IdentityRequest(BaseModel):
    """Identity signals for the /identity/resolve endpoint."""
    email: Optional[str] = None
    phone: Optional[str] = None
    name: Optional[str] = None
    instagram: Optional[str] = None


class IdentityResponse(BaseModel):
    """Result of identity resolution, including action and signal breakdown."""
    matched_author_id: Optional[str] = None
    confidence: float
    action: Literal["auto_link", "verify_manually", "create_new"]
    signals: list
    reasoning: str


class ResolveRequest(BaseModel):
    """Request schema for resolving escalated query reviews."""
    query_log_id: str
    approved_response: str
    rationale: Optional[str] = None
    reviewed_by: Optional[str] = None

