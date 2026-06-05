"""Restrict user input to English and French."""

import re

# CJK and related scripts not allowed in this project
_NON_LATIN_SCRIPTS = re.compile(
    r"[\u4e00-\u9fff\u3040-\u309f\u30a0-\u30ff\uac00-\ud7af"
    r"\u0600-\u06ff\u0400-\u04ff\u0370-\u03ff\u0590-\u05ff]"
)

_ALLOWED_LANGS = frozenset({"en", "fr"})

# Heuristic: mostly code / symbols — skip langdetect
_CODE_HINT = re.compile(
    r"(```|def\s+\w+|import\s+\w+|print\s*\(|class\s+\w+|#include|=>|:=|\{\}|\[\])"
)


def looks_like_code(text: str) -> bool:
    stripped = text.strip()
    if not stripped:
        return False
    if _CODE_HINT.search(stripped):
        return True
    letters = sum(c.isalpha() for c in stripped)
    return letters < max(8, len(stripped) * 0.25)


def validate_message_language(text: str) -> tuple[bool, str | None]:
    """
    Return (is_valid, rejection_reason).
    rejection_reason is 'cjk' or ISO 639-1 code when rejected.
    """
    if not text or not text.strip():
        return True, None

    if _NON_LATIN_SCRIPTS.search(text):
        return False, "cjk"

    if looks_like_code(text):
        return True, None

    try:
        from langdetect import detect, LangDetectException

        detected = detect(text)
        if detected not in _ALLOWED_LANGS:
            return False, detected
    except Exception:
        # Short or ambiguous text — allow (likely EN/FR)
        pass

    return True, None
