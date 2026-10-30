"""Behaviour of backend.shared.utils.env_utils."""

import pytest

from backend.shared.utils.env_utils import get_env, get_env_or_none

KEY = "SHARED_TEST_ENV_KEY"


def _set_or_unset(monkeypatch, value):
    if value is None:
        monkeypatch.delenv(KEY, raising=False)
    else:
        monkeypatch.setenv(KEY, value)


class TestGetEnv:
    def test_returns_stripped_value_when_set(self, monkeypatch):
        """Surrounding whitespace in .env values is ignored."""
        monkeypatch.setenv(KEY, "  llama3  ")

        assert get_env(KEY, "default") == "llama3"

    @pytest.mark.parametrize("value", [None, "", "   "], ids=["unset", "empty", "blank"])
    def test_falls_back_to_default_when_unset_or_blank(self, value, monkeypatch):
        """Unset, empty and whitespace-only values all count as 'not configured'."""
        _set_or_unset(monkeypatch, value)

        assert get_env(KEY, "default") == "default"

    def test_default_is_empty_string_when_not_given(self, monkeypatch):
        """Without an explicit default an unset variable yields an empty string."""
        monkeypatch.delenv(KEY, raising=False)

        assert get_env(KEY) == ""


class TestGetEnvOrNone:
    def test_returns_stripped_value_when_set(self, monkeypatch):
        """A configured value is returned stripped."""
        monkeypatch.setenv(KEY, " sk-123 ")

        assert get_env_or_none(KEY) == "sk-123"

    @pytest.mark.parametrize("value", [None, "", "\t "], ids=["unset", "empty", "blank"])
    def test_returns_none_when_unset_or_blank(self, value, monkeypatch):
        """Unset, empty and whitespace-only values are None, so callers can test `is None`."""
        _set_or_unset(monkeypatch, value)

        assert get_env_or_none(KEY) is None
