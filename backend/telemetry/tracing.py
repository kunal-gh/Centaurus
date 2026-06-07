"""
Centaurus Telemetry — Wave 2 Langfuse Observability Layer.

Wraps the entire chat pipeline with distributed traces so every LLM call,
retrieval step, identity resolution, and confidence score is visible in the
Langfuse dashboard (latency, token count, cost, retrieval scores).

Configuration (via .env):
  LANGFUSE_PUBLIC_KEY  — from Langfuse dashboard (cloud or self-hosted)
  LANGFUSE_SECRET_KEY  — from Langfuse dashboard
  LANGFUSE_HOST        — default: https://cloud.langfuse.com
                         set to http://localhost:3000 for self-hosted

If keys are absent, all tracing calls are no-ops — the rest of the app
is completely unaffected. This ensures zero coupling between observability
and the core business logic.

Usage pattern:
  trace = start_trace(name="chat", input={"query": ...}, session_id=...)
  span  = start_span(trace, name="kb_retrieval", input={"query": ...})
  end_span(span, output={...}, metadata={...})
  end_trace(trace, output={...})
"""
import os
import time
from typing import Any, Dict, Optional

# ─── Langfuse Client Singleton ────────────────────────────────────────────────

_LANGFUSE = None
_LANGFUSE_ENABLED = None


def _get_langfuse():
    """
    Lazy-initialises the Langfuse client.
    Returns None if credentials are not configured (graceful degradation).
    """
    global _LANGFUSE, _LANGFUSE_ENABLED

    if _LANGFUSE_ENABLED is not None:
        return _LANGFUSE  # Already resolved

    public_key = os.getenv("LANGFUSE_PUBLIC_KEY", "")
    secret_key = os.getenv("LANGFUSE_SECRET_KEY", "")
    host = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")

    if not public_key or not secret_key:
        print("[Telemetry] Langfuse keys not set — tracing disabled.")
        _LANGFUSE_ENABLED = False
        return None

    try:
        from langfuse import Langfuse
        _LANGFUSE = Langfuse(
            public_key=public_key,
            secret_key=secret_key,
            host=host,
        )
        _LANGFUSE_ENABLED = True
        print(f"[Telemetry] Langfuse tracing enabled → {host}")
    except Exception as e:
        print(f"[Telemetry] Langfuse init failed: {e} — tracing disabled.")
        _LANGFUSE_ENABLED = False

    return _LANGFUSE


# ─── Trace Lifecycle ──────────────────────────────────────────────────────────

def start_trace(
    name: str,
    input: Optional[Dict[str, Any]] = None,
    session_id: Optional[str] = None,
    user_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
):
    """
    Opens a new top-level Langfuse trace for a single request.
    Returns the trace object (or None if tracing is disabled).

    The trace maps 1-to-1 with an incoming /chat request.
    """
    lf = _get_langfuse()
    if not lf:
        return None
    try:
        return lf.trace(
            name=name,
            input=input or {},
            session_id=session_id,
            user_id=user_id,
            metadata=metadata or {},
        )
    except Exception as e:
        print(f"[Telemetry] start_trace failed: {e}")
        return None


def get_trace_id(trace) -> Optional[str]:
    """Extract the trace ID string from a Langfuse trace object."""
    if trace is None:
        return None
    try:
        return trace.id
    except Exception:
        return None


# ─── Span Lifecycle ────────────────────────────────────────────────────────────

def start_span(
    trace,
    name: str,
    input: Optional[Dict[str, Any]] = None,
    metadata: Optional[Dict[str, Any]] = None,
):
    """
    Opens a child span under the given trace.
    Each pipeline stage (intent, identity, retrieval, generation) gets its own span.
    Returns the span object (or None if tracing is disabled).
    """
    if trace is None:
        return None
    try:
        return trace.span(
            name=name,
            input=input or {},
            metadata=metadata or {},
            start_time=_now_iso(),
        )
    except Exception as e:
        print(f"[Telemetry] start_span({name}) failed: {e}")
        return None


def end_span(
    span,
    output: Optional[Dict[str, Any]] = None,
    metadata: Optional[Dict[str, Any]] = None,
    level: str = "DEFAULT",
):
    """
    Closes the span with output data and optional extra metadata.
    level: "DEFAULT" | "WARNING" | "ERROR"
    """
    if span is None:
        return
    try:
        span.end(
            output=output or {},
            metadata=metadata or {},
            level=level,
            end_time=_now_iso(),
        )
    except Exception as e:
        print(f"[Telemetry] end_span failed: {e}")


# ─── Generation Span (LLM Calls) ──────────────────────────────────────────────

def log_generation(
    trace,
    name: str,
    model: str,
    prompt: str,
    completion: str,
    prompt_tokens: int = 0,
    completion_tokens: int = 0,
    metadata: Optional[Dict[str, Any]] = None,
):
    """
    Logs an LLM generation event as a Langfuse Generation span.
    Captures token usage so cost is tracked automatically in Langfuse.
    """
    if trace is None:
        return
    try:
        gen = trace.generation(
            name=name,
            model=model,
            input=prompt,
            output=completion,
            usage={
                "input": prompt_tokens,
                "output": completion_tokens,
                "unit": "TOKENS",
            },
            metadata=metadata or {},
        )
        gen.end()
    except Exception as e:
        print(f"[Telemetry] log_generation failed: {e}")


# ─── Trace Finalisation ────────────────────────────────────────────────────────

def end_trace(
    trace,
    output: Optional[Dict[str, Any]] = None,
    metadata: Optional[Dict[str, Any]] = None,
):
    """
    Finalises the top-level trace with the pipeline output.
    Flushes the Langfuse buffer so the trace is immediately visible.
    """
    if trace is None:
        return
    try:
        trace.update(output=output or {}, metadata=metadata or {})
        lf = _get_langfuse()
        if lf:
            lf.flush()
    except Exception as e:
        print(f"[Telemetry] end_trace failed: {e}")


# ─── Helpers ───────────────────────────────────────────────────────────────────

def _now_iso() -> str:
    """Returns the current UTC time as an ISO-8601 string."""
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


def timer() -> float:
    """Returns current monotonic time in seconds for latency measurement."""
    return time.monotonic()


def elapsed_ms(start: float) -> int:
    """Returns elapsed milliseconds since start (from timer())."""
    return int((time.monotonic() - start) * 1000)
