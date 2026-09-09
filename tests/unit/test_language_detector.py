"""Offline language classification, including ambiguous technical vocabulary."""

import socket
import unicodedata

import pytest

from talentaudit.services.language_detector import LanguageDetector


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Kinh nghiệm xây dựng mô hình với Python.", "vi"),
        ("Experience building models with Python.", "en"),
        ("Kỹ năng Python. Experience building models.", "mixed"),
        ("Python SQL Docker", "mixed"),
        ("", "mixed"),
        ("123 ---", "mixed"),
        (unicodedata.normalize("NFD", "Kỹ năng và kinh nghiệm"), "vi"),
    ],
)
def test_language_offline(
    text: str, expected: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    def blocked(*args: object, **kwargs: object) -> None:
        raise AssertionError("Network access is forbidden")

    monkeypatch.setattr(socket, "socket", blocked)
    monkeypatch.setattr(socket, "getaddrinfo", blocked)
    detector = LanguageDetector()
    assert detector.detect(text) == expected
    assert detector.detect(text) == detector.detect(text)
