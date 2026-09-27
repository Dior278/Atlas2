from pathlib import Path

import pytest
from pydantic import ValidationError

from aparte.settings import AppSettings


def test_secrets_file_precedence(tmp_path, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    env = tmp_path / ".env"
    secrets = tmp_path / ".Secrets"
    env.write_text('OPENAI_API_KEY="old-local-test"\n', encoding="utf-8")
    secrets.write_text('OPENAI_API_KEY="new-local-test"\n', encoding="utf-8")
    settings = AppSettings(_env_file=(env, secrets))
    assert settings.openai_token == "new-local-test"
    assert "new-local-test" not in repr(settings)


def test_published_environment_example_is_loadable(monkeypatch):
    monkeypatch.delenv("GRADIUM_STT_DELAY_FRAMES", raising=False)
    example = Path(__file__).resolve().parents[1] / ".env.example"
    settings = AppSettings(_env_file=example)
    assert settings.gradium_stt_delay_frames == 12


def test_gradium_delay_accepts_environment_string(monkeypatch):
    monkeypatch.setenv("GRADIUM_STT_DELAY_FRAMES", "16")
    assert AppSettings(_env_file=None).gradium_stt_delay_frames == 16


@pytest.mark.parametrize("value", ("9", "abc", "12.5"))
def test_gradium_delay_still_rejects_unsupported_values(monkeypatch, value):
    monkeypatch.setenv("GRADIUM_STT_DELAY_FRAMES", value)
    with pytest.raises(ValidationError):
        AppSettings(_env_file=None)
