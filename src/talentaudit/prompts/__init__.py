"""Versioned instructions included in the installed application package."""

from importlib.resources import files

from talentaudit.schemas.llm import PromptTemplate


def load_profile_prompt() -> PromptTemplate:
    """Load a fixed resource, not a user-controlled path or prompt version."""

    return PromptTemplate(
        name="profile_extractor",
        version="v1",
        instructions=files(__package__)
        .joinpath("profile_extractor_v1.md")
        .read_text(encoding="utf-8"),
    )
