"""
Capture routing: decide whether a capture should be processed by the local
Ollama backend or escalated to Claude.

This is a pure function with no state, deliberately simple so the routing
policy is easy to audit and override from config.yaml.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional


# Route labels
LOCAL = "local"
CLAUDE = "claude"
LOCAL_WITH_FALLBACK = "local_with_fallback"

_VALID_ROUTES = {LOCAL, CLAUDE, LOCAL_WITH_FALLBACK}


@dataclass
class RouteDecision:
    route: str            # one of LOCAL / CLAUDE / LOCAL_WITH_FALLBACK
    reason: str           # human-readable explanation for logs


def route_capture(
    capture: Dict[str, Any],
    routing_config: Optional[Dict[str, Any]] = None,
    has_documents: bool = False,
    has_images: bool = False,
) -> RouteDecision:
    """
    Decide the backend route for a capture.

    Default policy (cheap-first):
      1. PDFs (document_paths)           -> claude
      2. Source captures (type=='Source')-> claude
      3. Reflections (type=='Reflection')-> claude
      4. Images (image_paths)            -> local_with_fallback
      5. Everything else                 -> local

    Every branch is overridable via routing_config, where keys are:
      pdf | source | reflection | images | default
    and values are "local" | "claude" | "local_with_fallback".

    Args:
        capture: Capture dict (needs 'type' at minimum).
        routing_config: Optional override map from config.yaml (llm.routing).
        has_documents: Whether document_paths was non-empty.
        has_images: Whether image_paths was non-empty.

    Returns:
        RouteDecision with route label and reason string.
    """
    cfg = routing_config or {}
    capture_type = (capture.get("type") or "").strip()

    if has_documents:
        return _decide(cfg, "pdf", CLAUDE, "pdf capture routed to claude")

    if capture_type == "Source":
        return _decide(cfg, "source", CLAUDE, "source capture routed to claude")

    if capture_type == "Reflection":
        return _decide(
            cfg, "reflection", CLAUDE, "reflection capture routed to claude"
        )

    if has_images:
        return _decide(
            cfg,
            "images",
            LOCAL_WITH_FALLBACK,
            "image capture routed to local with claude fallback",
        )

    return _decide(
        cfg, "default", LOCAL, f"{capture_type or 'unknown'} routed to local (default)"
    )


def _decide(
    cfg: Dict[str, Any],
    key: str,
    default_route: str,
    default_reason: str,
) -> RouteDecision:
    """Apply a config override for `key` if present, else use the default."""
    override = cfg.get(key)
    if override is None:
        return RouteDecision(route=default_route, reason=default_reason)

    normalized = str(override).strip().lower()
    if normalized not in _VALID_ROUTES:
        raise ValueError(
            f"Invalid routing override for {key!r}: {override!r}. "
            f"Must be one of {sorted(_VALID_ROUTES)}."
        )
    return RouteDecision(
        route=normalized,
        reason=f"{default_reason} (overridden via routing.{key}={normalized})",
    )
