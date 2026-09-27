"""Opt-in Gradium round trip with synthetic speech; no microphone is accessed."""

import asyncio
import base64
import json
from array import array
from pathlib import Path

from aparte.workspace.adapters.gradium import GradiumSTT, GradiumTTS
from aparte.workspace.config import load_config


async def main():
    Path("tmp").mkdir(exist_ok=True)
    config = load_config()
    phrase = "Renard prépare le prototype pour notre démonstration."
    stt_config = next(p for p in config.voice.stt.providers if p.provider == "gradium")
    tts_config = next(p for p in config.voice.tts.providers if p.provider == "gradium")
    pcm_config = tts_config.model_copy(update={"output_format": "pcm"})
    audio = await GradiumTTS(pcm_config).synthesize(phrase, "fr")
    samples = array("h", base64.b64decode(audio.data_base64))
    ratio = audio.sample_rate // 24000
    assert ratio >= 1 and audio.sample_rate % 24000 == 0
    pcm = array(
        "h",
        (
            int(sum(samples[i : i + ratio]) / ratio)
            for i in range(0, len(samples) - ratio + 1, ratio)
        ),
    ).tobytes()
    turns = []

    async def final(text):
        turns.append(text)

    async def partial(_):
        pass

    async def event(*_):
        pass

    stt = GradiumSTT(stt_config)
    try:
        await stt.start(partial, final, event, "fr")
        for offset in range(0, len(pcm), 3840):
            await stt.send(pcm[offset : offset + 3840].ljust(3840, b"\0"))
            await asyncio.sleep(0.08)
        for _ in range(40):
            await stt.send(bytes(3840))
            await asyncio.sleep(0.08)
        assert "prototype" in " ".join(turns).lower(), (
            "No complete synthetic speech transcription"
        )
    finally:
        await stt.stop()
    opus = await GradiumTTS(tts_config).synthesize(
        "Le prototype est prêt à être relu.", "fr"
    )
    chunks, timings = [], []

    async def text_chunks():
        yield "Renard prépare "
        yield "le prototype."

    async def on_audio(data, rate, format):
        assert rate == 24000 and format == "pcm_24000"
        chunks.append(len(data))

    async def on_text(text, start, stop):
        assert "<flush>" not in text
        timings.append((start, stop))

    await asyncio.wait_for(
        GradiumTTS(tts_config).stream_chunks(text_chunks(), "fr", on_audio, on_text),
        timeout=30,
    )
    assert sum(chunks) > 0 and timings, "Streaming audio or timed subtitles missing"
    Path("tmp/workspace-voice-sample.json").write_text(
        opus.model_dump_json(), encoding="utf-8"
    )
    report = {
        "tts_pcm": bool(samples),
        "stt_turns": len(turns),
        "expected_word": True,
        "tts_browser_format": opus.format,
        "audio_bytes": len(base64.b64decode(opus.data_base64)),
        "streaming_chunks": len(chunks),
        "subtitle_timings": len(timings),
    }
    Path("tmp/workspace-voice-validation.json").write_text(
        json.dumps(report), encoding="utf-8"
    )
    print(json.dumps(report))


if __name__ == "__main__":
    asyncio.run(main())
