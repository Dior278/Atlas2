from typing import Literal

from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", ".Secrets"), env_file_encoding="utf-8-sig", extra="ignore"
    )

    openai_api_key: SecretStr = SecretStr("")
    openai_key: SecretStr = SecretStr("")
    openai_model: str = "gpt-4.1-mini"
    openai_research_model: str = "gpt-5-mini"
    gradium_api_key: SecretStr = SecretStr("")
    gradium_voice_id: str = "b35yykvVppLXyw_l"
    gradium_stt_language: Literal["fr", "en", "de", "es", "pt", "any"] = "fr"
    gradium_stt_delay_frames: Literal[7, 8, 10, 12, 14, 16, 20, 24, 32, 36, 48] = 16
    dust_api_key: SecretStr = SecretStr("")
    dust_workspace_id: str = ""
    dust_domain: str = "https://dust.tt"
    pipelex_api_key: SecretStr = SecretStr("")
    typesafe_api_key: SecretStr = SecretStr("")

    @field_validator("gradium_stt_delay_frames", mode="before")
    @classmethod
    def parse_gradium_stt_delay_frames(cls, value):
        # Environment and dotenv values arrive as strings. Literal[int] validates
        # membership but does not coerce them as an ordinary int field would.
        if (
            isinstance(value, str)
            and value.strip().isascii()
            and value.strip().isdigit()
        ):
            return int(value.strip())
        return value

    @field_validator("dust_domain")
    @classmethod
    def validate_dust_domain(cls, value: str) -> str:
        domain = value.strip().lower().rstrip("/")
        if domain in {"dust.tt", "eu.dust.tt"}:
            domain = "https://" + domain
        # Send credentials only to an official origin, never to redirects or
        # an arbitrary host accidentally pasted in the configuration.
        if domain not in {"https://dust.tt", "https://eu.dust.tt"}:
            raise ValueError(
                "DUST_DOMAIN doit être https://dust.tt ou https://eu.dust.tt"
            )
        return domain

    def key(self, name: str) -> str:
        value = getattr(self, name)
        raw = value.get_secret_value() if isinstance(value, SecretStr) else value
        raw = raw.strip()
        if not raw or raw.lower().startswith(
            ("ta_cle", "ton_workspace", "your_", "replace_")
        ):
            return ""
        return raw

    @property
    def openai_token(self) -> str:
        return self.key("openai_api_key") or self.key("openai_key")
