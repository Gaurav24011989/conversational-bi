
from app.i18n import (
    get_locale_name,
    normalize_locale,
    parse_accept_language,
    resolve_locale,
    t,
)


class TestNormalizeLocale:
    def test_canonical_codes(self):
        assert normalize_locale("en") == "en"
        assert normalize_locale("fr") == "fr"
        assert normalize_locale("de") == "de"
        assert normalize_locale("es") == "es"
        assert normalize_locale("hi") == "hi"
        assert normalize_locale("zh") == "zh"

    def test_aliases(self):
        assert normalize_locale("en-US") == "en"
        assert normalize_locale("zh-CN") == "zh"
        assert normalize_locale("zh-Hans") == "zh"
        assert normalize_locale("mandarin") == "zh"

    def test_unsupported_returns_none(self):
        assert normalize_locale("ja") is None
        assert normalize_locale("") is None
        assert normalize_locale(None) is None


class TestParseAcceptLanguage:
    def test_single_locale(self):
        assert parse_accept_language("fr") == "fr"

    def test_quality_values(self):
        assert parse_accept_language("de, en;q=0.9, fr;q=0.8") == "de"

    def test_unsupported_falls_back(self):
        assert parse_accept_language("ja, ko") is None


class TestResolveLocale:
    def test_request_locale_takes_priority(self):
        assert (
            resolve_locale(
                request_locale="fr",
                accept_language="de",
                user_preferred="es",
                org_default="hi",
            )
            == "fr"
        )

    def test_accept_language_second(self):
        assert (
            resolve_locale(
                request_locale=None,
                accept_language="de, en;q=0.5",
                user_preferred="es",
            )
            == "de"
        )

    def test_user_preference_third(self):
        assert resolve_locale(user_preferred="hi") == "hi"

    def test_org_default_fourth(self):
        assert resolve_locale(org_default="es") == "es"

    def test_falls_back_to_default(self):
        assert resolve_locale() == "en"


class TestTranslations:
    def test_english_fallback(self):
        assert "rate limit" in t("errors.user_rate_limit", "en").lower()

    def test_french_translation(self):
        assert t("errors.user_rate_limit", "fr") == "Limite de requêtes utilisateur dépassée"

    def test_hindi_translation(self):
        assert "उपयोगकर्ता" in t("errors.user_rate_limit", "hi")

    def test_mandarin_translation(self):
        assert "用户" in t("errors.user_rate_limit", "zh")

    def test_interpolation(self):
        message = t("errors.query_generation_failed", "en", detail="timeout")
        assert "timeout" in message


class TestLocaleNames:
    def test_known_locales(self):
        assert get_locale_name("fr") == "Français"
        assert get_locale_name("zh") == "中文"

    def test_unknown_falls_back_to_english_name(self):
        assert get_locale_name("xx") == "English"
