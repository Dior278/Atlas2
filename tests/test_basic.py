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
