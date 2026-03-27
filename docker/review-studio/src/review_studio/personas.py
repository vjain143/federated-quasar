from __future__ import annotations


PERSONA_LABELS = {
    "architect": "Senior Enterprise Architect",
    "engineer": "Senior Principal Engineer",
    "test": "Principal Test Strategist",
}


def persona_prefix(persona: str) -> str:
    return PERSONA_LABELS.get(persona, PERSONA_LABELS["engineer"])


def render_comment(
    *,
    persona: str,
    severity: str,
    title: str,
    why_it_matters: str,
    recommendation: str | None = None,
) -> str:
    prefix = persona_prefix(persona)
    if persona == "architect":
        base = (
            f"{prefix} review: {title}. "
            f"From an enterprise architecture standpoint, {why_it_matters}"
        )
    elif persona == "test":
        base = (
            f"{prefix} review: {title}. "
            f"This creates a regression risk because {why_it_matters}"
        )
    else:
        base = (
            f"{prefix} review: {title}. "
            f"In production terms, {why_it_matters}"
        )

    if recommendation:
        return f"[{severity.upper()}] {base} Recommended action: {recommendation}"
    return f"[{severity.upper()}] {base}"
