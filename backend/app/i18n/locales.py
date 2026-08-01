"""Locale resolution and translation helpers for multi-lingual conversational BI."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from app.config import settings

# BCP-47 primary tags and common aliases → canonical locale code
_LOCALE_ALIASES: dict[str, str] = {
    "en": "en",
    "en-us": "en",
    "en-gb": "en",
    "fr": "fr",
    "fr-fr": "fr",
    "de": "de",
    "de-de": "de",
    "es": "es",
    "es-es": "es",
    "hi": "hi",
    "hi-in": "hi",
    "zh": "zh",
    "zh-cn": "zh",
    "zh-hans": "zh",
    "zh-hant": "zh",
    "zh-tw": "zh",
    "mandarin": "zh",
    "cmn": "zh",
}

LOCALE_INFO: dict[str, dict[str, str]] = {
    "en": {"name": "English", "native_name": "English"},
    "fr": {"name": "French", "native_name": "Français"},
    "de": {"name": "German", "native_name": "Deutsch"},
    "es": {"name": "Spanish", "native_name": "Español"},
    "hi": {"name": "Hindi", "native_name": "हिन्दी"},
    "zh": {"name": "Mandarin Chinese", "native_name": "中文"},
}

_TRANSLATIONS_DIR = Path(__file__).parent / "translations"


def get_supported_locales() -> list[str]:
    return list(settings.supported_locales)


def is_supported_locale(locale: str) -> bool:
    return normalize_locale(locale) is not None


def normalize_locale(locale: str | None) -> str | None:
    if not locale:
        return None
    normalized = locale.strip().lower().replace("_", "-")
    if not normalized:
        return None
    canonical = _LOCALE_ALIASES.get(normalized)
    if canonical and canonical in settings.supported_locales:
        return canonical
    primary = normalized.split("-", 1)[0]
    canonical = _LOCALE_ALIASES.get(primary)
    if canonical and canonical in settings.supported_locales:
        return canonical
    return None


def parse_accept_language(header: str | None) -> str | None:
    """Parse an Accept-Language header and return the best supported locale."""
    if not header:
        return None
    candidates: list[tuple[float, str]] = []
    for part in header.split(","):
        token = part.strip()
        if not token:
            continue
        if ";q=" in token:
            lang, _, q_value = token.partition(";q=")
            try:
                quality = float(q_value.strip())
            except ValueError:
                quality = 0.0
        else:
            lang = token
            quality = 1.0
        locale = normalize_locale(lang)
        if locale:
            candidates.append((quality, locale))
    if not candidates:
        return None
    candidates.sort(key=lambda item: item[0], reverse=True)
    return candidates[0][1]


def resolve_locale(
    *,
    request_locale: str | None = None,
    accept_language: str | None = None,
    user_preferred: str | None = None,
    org_default: str | None = None,
) -> str:
    """Resolve locale using explicit request > Accept-Language > user > org > default."""
    for candidate in (
        request_locale,
        parse_accept_language(accept_language),
        user_preferred,
        org_default,
        settings.default_locale,
    ):
        locale = normalize_locale(candidate)
        if locale:
            return locale
    return settings.default_locale


def get_locale_name(locale: str) -> str:
    info = LOCALE_INFO.get(locale, LOCALE_INFO["en"])
    return info["native_name"]


@lru_cache
def _load_catalog(locale: str) -> dict[str, str]:
    path = _TRANSLATIONS_DIR / f"{locale}.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def t(key: str, locale: str, **kwargs: str) -> str:
    """Translate a message key for the given locale, falling back to English."""
    catalog = _load_catalog(locale)
    message = catalog.get(key) or _load_catalog("en").get(key) or key
    if kwargs:
        try:
            return message.format(**kwargs)
        except (KeyError, IndexError):
            return message
    return message
