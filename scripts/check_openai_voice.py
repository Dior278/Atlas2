"""Opt-in OpenAI voice smoke adapted from Atlas 4e0823f.

Synthetic phrase, no microphone or user meeting. Consumes provider credits.
Does not change the configured primary voice provider.
"""

import asyncio
import base64
import json
from pathlib import Path

from aparte.workspace.adapters.openai_stt import OpenAISTT
from aparte.workspace.adapters.openai_tts import OpenAITTS
from aparte.workspace.config import load_config


async def main():
    Path("tmp").mkdir(exist_ok=True)
    config = load_config()
    stt_config = next(p for p in config.voice.stt.providers if p.provider == "openai")
    tts_config = next(p for p in config.voice.tts.providers if p.provider == "openai")
    stt = OpenAISTT(stt_config)
    turns = asyncio.Queue()

    async def ignore(*_):
        pass

    try:
        audio = await asyncio.wait_for(
            OpenAITTS(tts_config).synthesize(
                "Atlas, le prototype est prêt pour la démonstration.", "fr"
            ),
            45,
        )
        pcm = base64.b64decode(audio.data_base64)
        await asyncio.wait_for(stt.start(ignore, turns.put, ignore, "fr"), 15)
        for offset in range(0, len(pcm), 3840):
            await stt.send(pcm[offset : offset + 3840].ljust(3840, b"\0"))
            await asyncio.sleep(0.08)
        for _ in range(20):
            await stt.send(bytes(3840))
            await asyncio.sleep(0.08)
        transcript = await asyncio.wait_for(turns.get(), 20)
        assert "prototype" in transcript.lower(), "Expected synthetic word missing"
        report = {
            "tts_bytes": len(pcm),
            "stt_expected_word": True,
            "provider": "openai",
            "microphone": False,
        }
        Path("tmp/openai-voice-validation.json").write_text(
            json.dumps(report), encoding="utf-8"
        )
        print(json.dumps(report))
    finally:
        await stt.stop()


if __name__ == "__main__":
    asyncio.run(main())
