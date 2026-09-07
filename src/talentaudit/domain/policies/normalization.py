"""Canonicalization helpers for deterministic comparisons."""


def normalize_skill(value: str) -> str:
    """Normalize skill labels without applying any LLM or taxonomy inference."""

    return " ".join(value.casefold().split())
