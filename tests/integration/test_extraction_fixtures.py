"""Exercise fixed bilingual fixture labels, never compute model-quality metrics."""

import json
import socket
from hashlib import sha256
from pathlib import Path
from typing import Literal

import pytest
from pydantic import BaseModel, ConfigDict, Field

from talentaudit.adapters.llm.fake import FakeLLMClient
from talentaudit.config import Settings
from talentaudit.schemas.document import DocumentUpload
from talentaudit.schemas.evidence import EvidenceRef
from talentaudit.schemas.extraction import ExtractedProfile, SkillClaim
from talentaudit.services.document_parser import DocumentParser
from talentaudit.services.document_validator import DocumentValidator
from talentaudit.services.profile_extractor import ProfileExtractor

FIXTURES = Path(__file__).parents[1] / "fixtures" / "documents"


class FixtureLabel(BaseModel):
    model_config = ConfigDict(extra="forbid")
    path: str = Field(pattern=r"^(vi|en)_[1-5]\.txt$")
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    language: Literal["vi", "en"]
    skills: list[str]
    years: None
    expected_status: Literal["SUCCESS"]


class FixtureManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    version: str
    purpose: str
    fixtures: list[FixtureLabel]


MANIFEST = FixtureManifest.model_validate_json(
    (FIXTURES / "manifest.json").read_bytes()
)


def test_manifest_covers_ten_unique_bilingual_files() -> None:
    assert len({label.path for label in MANIFEST.fixtures}) == 10
    assert sum(label.language == "vi" for label in MANIFEST.fixtures) == 5
    assert sum(label.language == "en" for label in MANIFEST.fixtures) == 5


@pytest.mark.parametrize("label", MANIFEST.fixtures, ids=lambda label: label.path)
def test_validate_parse_extract_offline(
    label: FixtureLabel, monkeypatch, caplog
) -> None:
    def deny(*args, **kwargs):
        raise AssertionError("Network forbidden in fixture acceptance run")

    monkeypatch.setattr(socket, "getaddrinfo", deny)
    monkeypatch.setattr(socket.socket, "connect", deny)
    content = (FIXTURES / label.path).read_bytes()
    assert sha256(content).hexdigest() == label.sha256
    settings = Settings(_env_file=None)
    validated = DocumentValidator(settings).validate(
        DocumentUpload(
            filename=label.path,
            declared_mime_type="text/plain",
            content=content,
        )
    )
    parsed = DocumentParser(settings).parse(validated)
    assert parsed.document_language == label.language
    # Labels are fixed above. Offsets are resolved against the pinned exact bytes.
    claims = []
    for skill in label.skills:
        start = parsed.text.index(skill)
        claims.append(
            SkillClaim(
                skill=skill,
                status="KNOWN",
                years=label.years,
                experience_evidence=[],
                skill_evidence=[
                    EvidenceRef(
                        document_id=parsed.document_id,
                        section="skills",
                        start=start,
                        end=start + len(skill),
                        text=skill,
                    )
                ],
            )
        )
    fake = FakeLLMClient([ExtractedProfile(claims=claims).model_dump_json()])
    outcome = ProfileExtractor(fake).extract(parsed)
    assert outcome.status == label.expected_status
    assert outcome.profile is not None
    assert outcome.profile.skills == [skill.casefold() for skill in label.skills]
    assert outcome.profile.experience_years == {}
    assert outcome.sha256 == validated.sha256 == label.sha256
    assert outcome.document_id == validated.document_id
    assert outcome.attempts == len(fake.calls) == 1
    for refs in outcome.profile.skill_evidence.values():
        for ref in refs:
            assert parsed.text[ref.start : ref.end] == ref.text
    assert parsed.text not in caplog.text
    assert json.loads(outcome.model_dump_json())["status"] == "SUCCESS"
