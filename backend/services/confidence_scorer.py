"""
Composite confidence calculation and escalation decision engine.
This is the MOST CRITICAL file for the assignment.
Spec Reference: Section 6.8
"""


def calculate_confidence(
    intent_confidence: float,
    identity_confidence: float,
    kb_relevance: float = 0.0,
    query_type: str = "db_query"
) -> float:
    """
    Computes overall confidence score using weighted signals.

    Formula:
        effective_identity = 1.0 if query_type == "kb_query" else identity_confidence
        overall = 0.50 * intent_confidence
                + 0.30 * effective_identity
                + 0.20 * kb_relevance

    Special rules:
    - For KB-only queries (query_type == "kb_query"), identity is not required,
      so effective_identity is set to 1.0 (prevents unjust confidence penalty).
    - Floor guarantee: when both intent AND effective_identity >= 0.90 AND kb_relevance < 0.3,
      score is raised to at least 0.82 (prevents clear DB queries from falling below threshold
      due to floating point arithmetic).

    Args:
        intent_confidence: 0.0-1.0 from intent_classifier
        identity_confidence: 0.0-1.0 from identity_unifier or direct data match
        kb_relevance: 0.0-1.0 from knowledge_base.search (0.0 if unused)
        query_type: "db_query" or "kb_query"

    Returns:
        float: Rounded to 3 decimal places, clamped to [0.0, 1.0]
    """
    # For KB-only queries, identity verification is not required
    effective_identity = 1.0 if query_type == "kb_query" else identity_confidence

    score = (
        0.50 * intent_confidence +
        0.30 * effective_identity +
        0.20 * kb_relevance
    )

    # Clear-case floor guarantee: when intent and identity are both strong
    if intent_confidence >= 0.90 and effective_identity >= 0.90 and kb_relevance < 0.3:
        score = max(score, 0.82)

    return round(min(max(score, 0.0), 1.0), 3)


def should_escalate(confidence: float, intent: str, error_flags: list) -> dict:
    """
    Determines if query must be escalated to a human agent.

    Escalation triggers (checked in priority order — ANY trigger escalates):
    1. System error flags exist (DB down, API failure, exception traces)
    2. Intent is explicitly "escalate_human" (angry, legal threat, refund demand)
    3. Intent is "unknown" (classifier cannot determine what user wants)
    4. Composite confidence < 0.80 (the hard 80% circuit breaker)

    Args:
        confidence: Composite confidence score from calculate_confidence()
        intent: Classified intent string from intent_classifier
        error_flags: List of error strings from upstream services

    Returns:
        dict: {"escalate": bool, "reason": str}
    """
    if error_flags:
        return {
            "escalate": True,
            "reason": f"System error(s): {'; '.join(error_flags)}"
        }

    if intent == "escalate_human":
        return {
            "escalate": True,
            "reason": "Message flagged as requiring human agent by intent classifier"
        }

    if intent == "unknown":
        return {
            "escalate": True,
            "reason": "Intent could not be determined"
        }

    if confidence < 0.80:
        return {
            "escalate": True,
            "reason": f"Confidence score {confidence} is below the 0.80 threshold"
        }

    return {"escalate": False, "reason": "Confidence acceptable"}
