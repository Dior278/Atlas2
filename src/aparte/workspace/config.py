from __future__ import annotations

import json
import os
from importlib.resources import files
from pathlib import Path
from typing import Literal

from dotenv import dotenv_values
from pydantic import BaseModel, ConfigDict, Field, model_validator

from aparte.workspace.languages import AtlasLanguage
from aparte.workspace.prompts import PROMPTS as PROMPTS

PROJECT_ROOT = Path(__file__).resolve().parents[3]
USER_CONFIG = PROJECT_ROOT / ".data" / "config.json"


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ProductConfig(StrictModel):
    project_id: str
    display_name: str
    companion_name: str
    protocol_version: int


class ServerConfig(StrictModel):
    host: str = "127.0.0.1"
    port: int = Field(default=8765, ge=1, le=65535)


class SessionConfig(StrictModel):
    language: AtlasLanguage = "en"
    notes_interval_seconds: float = Field(default=20, gt=0)


class PolicyConfig(StrictModel):
    stable_floor_gap_seconds: float = Field(default=1.5, ge=0)
    direct_floor_gap_seconds: float = Field(default=0.8, ge=0)
    awaited_floor_gap_seconds: float = Field(default=3.0, ge=0)
    unsolicited_speech_cooldown_seconds: float = Field(default=90, ge=0)
    research_max_concurrency: int = Field(default=3, ge=1, le=16)
    max_tool_steps: int = Field(default=4, ge=1, le=16)
    mission_timeout_seconds: float = Field(default=120, ge=1, le=600)


class StorageConfig(StrictModel):
    database_path: str = ""

    def resolved_path(self) -> Path:
        if self.database_path:
            return Path(self.database_path).expanduser()
        return Path(
            os.environ.get(
                "APARTE_DATABASE_PATH", PROJECT_ROOT / ".data" / "aparte.sqlite3"
            )
        )


class STTModelConfig(StrictModel):
    id: str
    provider: Literal["gradium", "openai"] | None = None
    endpoint: str
    secret_env: str
    model: str | None = None
    input_format: str = "pcm_24000"
    language: str = "en"
    delay_in_frames: int = Field(default=16, ge=7, le=55)
    rotate_after_seconds: float = Field(default=285, gt=0, le=3600)
    noise_reduction: Literal["near_field", "far_field"] = "far_field"
    silence_duration_ms: int = Field(default=500, ge=200, le=2000)

    @model_validator(mode="after")
    def resolve_reference(self) -> STTModelConfig:
        try:
            inferred_provider, inferred_model = self.id.split("/", 1)
        except ValueError as error:
            raise ValueError("STT model IDs must use provider/model") from error
        if inferred_provider not in {"gradium", "openai"}:
            raise ValueError(f"unsupported STT provider: {inferred_provider}")
        if self.provider is not None and self.provider != inferred_provider:
            raise ValueError("STT provider conflicts with its provider/model ID")
        if self.model is not None and self.model != inferred_model:
            raise ValueError("STT model conflicts with its provider/model ID")
        object.__setattr__(self, "provider", inferred_provider)
        object.__setattr__(self, "model", inferred_model)
        return self


class STTRegistryConfig(StrictModel):
    active: str
    providers: list[STTModelConfig]

    @model_validator(mode="after")
    def validate_registry(self) -> STTRegistryConfig:
        ids = [item.id for item in self.providers]
        if len(ids) != len(set(ids)):
            raise ValueError("STT model IDs must be unique")
        if self.active not in ids:
            raise ValueError("voice.stt.active must reference a registered STT model")
        return self

    def ordered(self) -> list[STTModelConfig]:
        active = next(item for item in self.providers if item.id == self.active)
        return [active, *(item for item in self.providers if item.id != self.active)]


class TTSModelConfig(StrictModel):
    id: str
    provider: Literal["gradium", "openai"] | None = None
    endpoint: str
    secret_env: str
    voice_id_env: str = ""
    voice_id: str = "marin"
    model: str | None = None
    output_format: str = "pcm_24000"
    temperature: float = Field(default=0.9, ge=0, le=1.4)
    cfg_coef: float = Field(default=2.2, ge=1, le=4)
    padding_bonus: float = Field(default=-0.5, ge=-4, le=4)
    instructions: str = (
        "Speak naturally and conversationally. Never read punctuation or markup aloud."
    )

    @model_validator(mode="after")
    def resolve_reference(self) -> TTSModelConfig:
        try:
            inferred_provider, inferred_model = self.id.split("/", 1)
        except ValueError as error:
            raise ValueError("TTS model IDs must use provider/model") from error
        if inferred_provider not in {"gradium", "openai"}:
            raise ValueError(f"unsupported TTS provider: {inferred_provider}")
        if self.provider is not None and self.provider != inferred_provider:
            raise ValueError("TTS provider conflicts with its provider/model ID")
        if self.model is not None and self.model != inferred_model:
            raise ValueError("TTS model conflicts with its provider/model ID")
        object.__setattr__(self, "provider", inferred_provider)
        object.__setattr__(self, "model", inferred_model)
        return self


class TTSRegistryConfig(StrictModel):
    active: str
    providers: list[TTSModelConfig]

    @model_validator(mode="after")
    def validate_registry(self) -> TTSRegistryConfig:
        ids = [item.id for item in self.providers]
        if len(ids) != len(set(ids)):
            raise ValueError("TTS model IDs must be unique")
        if self.active not in ids:
            raise ValueError("voice.tts.active must reference a registered TTS model")
        return self

    def ordered(self) -> list[TTSModelConfig]:
        active = next(item for item in self.providers if item.id == self.active)
        return [active, *(item for item in self.providers if item.id != self.active)]


class VoiceConfig(StrictModel):
    stt: STTRegistryConfig
    tts: TTSRegistryConfig

    @model_validator(mode="before")
    @classmethod
    def migrate_single_provider(cls, value):
        if not isinstance(value, dict):
            return value
        migrated = dict(value)
        for kind in ("stt", "tts"):
            old = migrated.get(kind)
            if isinstance(old, dict) and "providers" not in old and "provider" in old:
                provider = dict(old)
                provider["id"] = f"{provider['provider']}/{provider['model']}"
                migrated[kind] = {"active": provider["id"], "providers": [provider]}
        return migrated


class DecisionConfig(StrictModel):
    provider: Literal["typesafe"]
    endpoint: str
    secret_env: str
    model: str
    expected_speaker_latency_ms: int = Field(default=1100, ge=0)


class LLMModelConfig(StrictModel):
    id: str
    provider: Literal["openai", "opencode-zen"] | None = None
    model: str | None = None
    endpoint: str
    transport: Literal["responses", "chat_completions"]
    secret_env: str
    reasoning_effort: Literal["none", "minimal", "low", "medium", "high"] | None = None
    max_output_tokens: int = Field(ge=1, le=8192)
    max_concurrency: int = Field(default=2, ge=1, le=16)
    timeout_seconds: float | None = Field(default=None, gt=0)
    input_usd_per_million_tokens: float = Field(ge=0)
    output_usd_per_million_tokens: float = Field(ge=0)

    @model_validator(mode="after")
    def resolve_reference(self) -> LLMModelConfig:
        try:
            inferred_provider, inferred_model = self.id.split("/", 1)
        except ValueError as error:
            raise ValueError("LLM model IDs must use provider/model") from error
        if inferred_provider not in {"openai", "opencode-zen"}:
            raise ValueError(f"unsupported LLM provider: {inferred_provider}")
        if self.provider is not None and self.provider != inferred_provider:
            raise ValueError("LLM provider conflicts with its provider/model ID")
        if self.model is not None and self.model != inferred_model:
            raise ValueError("LLM model conflicts with its provider/model ID")
        object.__setattr__(self, "provider", inferred_provider)
        object.__setattr__(self, "model", inferred_model)
        return self


class LLMRolesConfig(StrictModel):
    speaker: str
    worker: str
    notes: str
    board: str
    naming: str
    fallback: str


class LLMConfig(StrictModel):
    roles: LLMRolesConfig
    timeout_seconds: float = Field(default=30, gt=0)
    max_request_cost_usd: float = Field(default=6, ge=0)
    models: list[LLMModelConfig]

    @model_validator(mode="after")
    def validate_registry(self) -> LLMConfig:
        ids = [item.id for item in self.models]
        if len(ids) != len(set(ids)):
            raise ValueError("LLM model IDs must be unique")
        for role, model_id in self.roles.model_dump().items():
            if model_id not in ids:
                raise ValueError(f"llm.roles.{role} must reference a registered model")
        return self

    @property
    def active_model(self) -> str:
        return self.roles.speaker

    def select(self, model_id: str | None = None) -> LLMModelConfig:
        selected = model_id or self.roles.worker
        return next(item for item in self.models if item.id == selected)


class JinkoConfig(StrictModel):
    enabled: bool = True
    base_url: str
    secret_env: str


class ExaConfig(StrictModel):
    enabled: bool = True
    endpoint: str
    secret_env: str
    search_type: Literal[
        "instant", "fast", "auto", "deep-lite", "deep", "deep-reasoning"
    ] = "auto"
    num_results: int = Field(default=5, ge=1, le=20)


class ToolsConfig(StrictModel):
    jinko: JinkoConfig
    exa: ExaConfig


class AppConfig(StrictModel):
    server: ServerConfig
    session: SessionConfig
    policy: PolicyConfig
    storage: StorageConfig
    voice: VoiceConfig
    decision: DecisionConfig
    llm: LLMConfig
    tools: ToolsConfig


def default_config_text() -> str:
    return (
        files("aparte.workspace")
        .joinpath("default_config.json")
        .read_text(encoding="utf-8")
    )


def load_product() -> ProductConfig:
    path = Path(os.environ.get("ATLAS_PRODUCT_FILE", PROJECT_ROOT / "product.json"))
    return ProductConfig.model_validate_json(path.read_text(encoding="utf-8"))


def load_config(path: Path | None = None) -> AppConfig:
    from aparte.settings import AppSettings

    selected = path or Path(
        os.environ.get(
            "ATLAS_CONFIG", os.environ.get("APARTE_CONFIG_FILE", USER_CONFIG)
        )
    )
    values = (
        json.loads(selected.read_text(encoding="utf-8"))
        if selected.exists()
        else json.loads(default_config_text())
    )
    if not selected.exists():
        settings = AppSettings()
        values["server"]["port"] = 8765
        values["session"]["language"] = "fr"
        for provider in values["voice"]["stt"]["providers"]:
            provider["language"] = settings.gradium_stt_language
            if provider["provider"] == "gradium":
                provider["delay_in_frames"] = settings.gradium_stt_delay_frames
        for provider in values["voice"]["tts"]["providers"]:
            if provider["provider"] == "gradium":
                provider["voice_id"] = settings.gradium_voice_id
        # Use the user's configured model for each Atlas role by default.
        model_id = f"openai/{settings.openai_model}"
        if not any(m["id"] == model_id for m in values["llm"]["models"]):
            values["llm"]["models"].append(
                dict(
                    id=model_id,
                    endpoint="https://api.openai.com/v1/responses",
                    transport="responses",
                    secret_env="OPENAI_API_KEY",
                    max_output_tokens=4096,
                    max_concurrency=6,
                    input_usd_per_million_tokens=0,
                    output_usd_per_million_tokens=0,
                )
            )
        values["llm"]["roles"] = {
            role: model_id for role in LLMRolesConfig.model_fields
        }
    elif "active_model" in values.get("llm", {}):
        # Migrate Sidecar/Aparté v9 settings in memory; keep the original file intact.
        llm = values["llm"]
        names = {}
        for model in llm["models"]:
            old_id = model["id"]
            model["id"] = f"{model['provider']}/{model['model']}"
            names[old_id] = model["id"]
        speaker = names[llm.pop("active_model")]
        worker = (
            names[llm.pop("utility_model", "")]
            if llm.get("utility_model") in names
            else speaker
        )
        llm.pop("utility_model", None)
        llm.pop("utility_timeout_seconds", None)
        llm["models"] = list({m["id"]: m for m in llm["models"]}.values())
        llm["roles"] = {
            role: speaker if role == "speaker" else worker
            for role in LLMRolesConfig.model_fields
        }
        values["session"].pop("assistant_name", None)
        values["policy"] = {
            k: v for k, v in values["policy"].items() if k in PolicyConfig.model_fields
        }
        values["decision"].pop("addressed_threshold", None)
    return AppConfig.model_validate(values)


def secret(name: str) -> str | None:
    value = os.environ.get(name)
    if value is None:
        local = {}
        for path in (PROJECT_ROOT / ".env", PROJECT_ROOT / ".Secrets"):
            if path.is_file():
                local.update(dotenv_values(path, encoding="utf-8-sig"))
        value = local.get(name)
        if not value and name == "OPENAI_API_KEY":
            value = os.environ.get("OPENAI_KEY") or local.get("OPENAI_KEY")
    return value.strip() if value and value.strip() else None
