"""Small offline VI/EN heuristic; not a general-purpose language classifier."""

import re
import unicodedata

from talentaudit.schemas.document import DocumentLanguage

# Language markers exclude shared technical names (Python, SQL, Docker, ...).
_VI = frozenset(
    (
        "kinh nghiệm kỹ năng dự án học vấn phát triển xây dựng dữ liệu "
        "mô hình kiểm thử triển khai và với trong của tôi"
    ).split()
)
_EN = frozenset(
    (
        "experience skills projects education developed built trained deployed "
        "testing working with and the for in of profile synthetic page"
    ).split()
)


class LanguageDetector:
    """Classify lexical evidence; mixed also represents insufficient evidence."""

    def detect(self, text: str) -> DocumentLanguage:
        """Normalize a temporary copy only, preserving the caller's source text."""
        tokens = set(
            re.findall(r"[^\W\d_]+", unicodedata.normalize("NFC", text).casefold())
        )
        has_vi = bool(tokens & _VI)
        has_en = bool(tokens & _EN)
        if has_vi and not has_en:
            return "vi"
        if has_en and not has_vi:
            return "en"
        return "mixed"
