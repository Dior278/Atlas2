import json

import httpx
import pytest

from aparte.workspace.adapters import openai_tts
from aparte.workspace.config import TTSModelConfig


@pytest.mark.parametrize(
    "chunks,valid", [([b"\x01", b"\x02\x03", b"\x04"], True), ([b"\x01"], False)]
)
async def test_pcm_transport_preserves_sample_boundaries(monkeypatch, chunks, valid):
    class Bytes(httpx.AsyncByteStream):
        async def __aiter__(self):
            for chunk in chunks:
                yield chunk

    def handle(request):
        payload = json.loads(request.content)
        assert payload["response_format"] == "pcm"
        assert payload["model"] == "gpt-4o-mini-tts"
        return httpx.Response(200, stream=Bytes())

    original_client = httpx.AsyncClient
    monkeypatch.setattr(
        openai_tts.httpx,
        "AsyncClient",
        lambda **kwargs: original_client(
            transport=httpx.MockTransport(handle), **kwargs
        ),
    )
    monkeypatch.setattr(openai_tts, "secret", lambda _: "fake-key")
    provider = openai_tts.OpenAITTS(
        TTSModelConfig(
            id="openai/gpt-4o-mini-tts",
            endpoint="https://openai.test/speech",
            secret_env="TEST",
        )
    )
    emitted = []

    async def receive(data, rate, format):
        assert len(data) % 2 == 0
        assert rate == 24000
        emitted.append(data)

    if valid:
        await provider.stream("Texte fictif", "fr", receive)
        assert b"".join(emitted) == b"\x01\x02\x03\x04"
    else:
        with pytest.raises(RuntimeError, match="truncated"):
            await provider.stream("Texte fictif", "fr", receive)
