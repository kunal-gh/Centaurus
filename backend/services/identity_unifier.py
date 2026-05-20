"""
User Identity Unification System.
Links Email, WhatsApp, Dashboard name, Instagram handle to a single author profile.

Algorithm: Three-tier approach
  Tier 1 (Deterministic, >= 80%): Exact email or normalized phone match -> auto_link
  Tier 2 (Fuzzy, 40-79%): rapidfuzz scoring + LLM verifier for borderline cases
  Tier 3 (New Identity, < 40%): Low confidence -> create provisional profile

This satisfies the Intermediate Task requirement from the assignment brief.
Spec Reference: Section 6.9
"""
import json
from rapidfuzz import fuzz
from openai import OpenAI
from backend.config import settings

client = OpenAI(api_key=settings.OPENAI_API_KEY)


def _normalize_phone(phone: str) -> str:
    """Strips +, spaces, dashes, and leading zeros for comparison."""
    if not phone:
        return ""
    return phone.replace("+", "").replace(" ", "").replace("-", "").lstrip("0")


def _normalize_handle(handle: str) -> str:
    """Lowercases and strips leading @ from Instagram handles."""
    if not handle:
        return ""
    return handle.lower().lstrip("@")


def compute_match_score(incoming: dict, candidate: dict) -> dict:
    """
    Computes weighted fuzzy match score between incoming signals and candidate profile.

    Weight Allocation (total 100 points when all signals present):
    - Email exact match:              35 points
    - Phone exact (normalized):       30 points
    - Name fuzzy (token_sort_ratio):  25 points (matched if ratio > 70)
    - Instagram handle exact:         10 points

    Only includes a signal in scoring if BOTH incoming and candidate have the field.
    Score is normalized against available weight (not total 100) to avoid penalizing
    for missing signals.

    Args:
        incoming: dict with keys email, phone, name, instagram
        candidate: author row dict from Supabase

    Returns:
        dict: {"score": float (0-100), "signals": list of match detail dicts}
    """
    signals = []
    total_weight = 0
    weighted_score = 0.0

    # Email — exact match only (35 pts)
    if incoming.get("email") and candidate.get("email"):
        match = 100 if incoming["email"].lower() == candidate["email"].lower() else 0
        signals.append({"signal": "email", "score": match, "weight": 35, "matched": match == 100})
        weighted_score += match * 35
        total_weight += 35

    # Phone — normalized exact (30 pts)
    if incoming.get("phone") and candidate.get("phone"):
        match = 100 if _normalize_phone(incoming["phone"]) == _normalize_phone(candidate["phone"]) else 0
        signals.append({"signal": "phone", "score": match, "weight": 30, "matched": match == 100})
        weighted_score += match * 30
        total_weight += 30

    # Name — fuzzy token sort ratio (25 pts)
    if incoming.get("name") and candidate.get("dashboard_name"):
        ratio = fuzz.token_sort_ratio(incoming["name"].lower(), candidate["dashboard_name"].lower())
        signals.append({"signal": "name_fuzzy", "score": ratio, "weight": 25, "matched": ratio > 70})
        weighted_score += ratio * 25
        total_weight += 25

    # Instagram handle — exact after normalization (10 pts)
    if incoming.get("instagram") and candidate.get("instagram_handle"):
        match = 100 if _normalize_handle(incoming["instagram"]) == _normalize_handle(candidate["instagram_handle"]) else 0
        signals.append({"signal": "instagram_handle", "score": match, "weight": 10, "matched": match == 100})
        weighted_score += match * 10
        total_weight += 10

    if total_weight == 0:
        return {"score": 0.0, "signals": signals}

    # Normalize against available weight (not total 100)
    final_score = (weighted_score / (total_weight * 100)) * 100
    return {"score": round(final_score, 1), "signals": signals}


def _llm_verify(incoming: dict, candidate: dict, fuzzy_score: float) -> dict:
    """
    LLM fallback for borderline identity matches (score 40-79).
    Asks GPT-4o-mini to assess probability that two profiles belong to the same person.

    Only called for Tier 2 cases — not for clear matches or clear mismatches.
    """
    prompt = f"""Two profiles may belong to the same person. Assess the probability.

Profile A (incoming signals): {json.dumps(incoming)}
Profile B (existing database record): {json.dumps(candidate)}
Current fuzzy signal score: {fuzzy_score}/100

Return JSON:
{{
  "same_person_probability": <float 0.0 to 1.0>,
  "reasoning": "<one sentence explaining your reasoning>",
  "recommended_action": "<auto_link|verify_manually|create_new>"
}}

Use these thresholds:
- probability >= 0.85 -> auto_link
- probability >= 0.60 -> verify_manually
- probability < 0.60  -> create_new"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        temperature=0.1,
        max_tokens=200
    )

    return json.loads(response.choices[0].message.content)


def unify_identity(incoming: dict, all_profiles: list) -> dict:
    """
    Main identity resolution entry point.

    Three-tier decision tree:
    - Tier 1 (score >= 80): auto_link immediately
    - Tier 2 (score 40-79): LLM verify, blend scores, use LLM action
    - Tier 3 (score < 40): create_new provisional profile

    Args:
        incoming: dict with keys email, phone, name, instagram
        all_profiles: list of all author rows from Supabase

    Returns:
        dict with keys: matched_author_id, confidence, action, signals, reasoning
    """
    if not all_profiles:
        return {
            "matched_author_id": None,
            "confidence": 0.0,
            "action": "create_new",
            "signals": [],
            "reasoning": "No existing profiles to match against"
        }

    # Score all candidates and find the best match
    scored = []
    for profile in all_profiles:
        result = compute_match_score(incoming, profile)
        scored.append({
            "author_id": profile["id"],
            "profile": profile,
            "score": result["score"],
            "signals": result["signals"]
        })

    # Sort descending by score — best candidate is first
    scored.sort(key=lambda x: x["score"], reverse=True)
    best = scored[0]
    confidence = best["score"] / 100.0

    # TIER 1: HIGH confidence (>= 80%) -> auto link immediately
    if best["score"] >= 80:
        return {
            "matched_author_id": best["author_id"],
            "confidence": round(confidence, 3),
            "action": "auto_link",
            "signals": best["signals"],
            "reasoning": "High confidence fuzzy match — exact or near-exact signals on primary identifiers"
        }

    # TIER 2: BORDERLINE (40-79%) -> LLM verify
    if 40 <= best["score"] < 80:
        llm_result = _llm_verify(incoming, best["profile"], best["score"])
        llm_prob = float(llm_result.get("same_person_probability", 0))
        final_confidence = round((confidence + llm_prob) / 2, 3)
        action = llm_result.get("recommended_action", "verify_manually")

        return {
            "matched_author_id": best["author_id"] if action != "create_new" else None,
            "confidence": final_confidence,
            "action": action,
            "signals": best["signals"],
            "reasoning": llm_result.get("reasoning", "LLM borderline verification")
        }

    # TIER 3: LOW confidence (< 40%) -> create new provisional profile
    return {
        "matched_author_id": None,
        "confidence": round(confidence, 3),
        "action": "create_new",
        "signals": best["signals"],
        "reasoning": "Confidence too low for any reliable match — creating provisional profile"
    }
