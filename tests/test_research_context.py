import asyncio
import json

import httpx
import pytest

from aparte.providers import LiveBackend, ProviderError
from aparte.settings import AppSettings
from aparte.weather import lookup_weather


@pytest.mark.parametrize("feature", ["PCLI", "ADM1", "RGN", ""])
def test_non_city_cannot_be_read_as_countrywide_weather(feature):
    async def scenario():
        requests = []

        def respond(request):
            requests.append(str(request.url))
            assert "geocoding" in request.url.host
            return httpx.Response(
                200,
                json={
                    "results": [
                        {
                            "name": "Italie",
                            "country": "Italie",
                            "country_code": "IT",
                            "feature_code": feature,
                            "latitude": 42.8,
                            "longitude": 12.8,
                            "population": 60000000,
                        }
                    ]
                },
            )

        async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
            finding = await lookup_weather(
                client, '{"location":"Italie","country_code":"IT"}'
            )
        assert len(requests) == 1
        assert "quelle ville" in finding.summary
        assert not finding.sources
        assert "degrés" not in finding.summary

    asyncio.run(scenario())


def test_web_receives_context_and_datetime_and_refuses_uncited_result():
    async def scenario():
        def respond(request):
            payload = json.loads(request.content)
            context = json.loads(payload["input"])
            assert (
                context["conversation"][-1]["text"]
                == "Correction : ABC désigne mon document."
            )
            assert context["current_datetime"]
            assert context["question"] == "Correction : ABC désigne mon document."
            assert "constraints" not in context
            assert payload["tool_choice"] == "required"
            return httpx.Response(
                200,
                json={
                    "status": "completed",
                    "output": [
                        {
                            "type": "message",
                            "content": [
                                {
                                    "type": "output_text",
                                    "text": "Oui sans conditions",
                                    "annotations": [],
                                }
                            ],
                        }
                    ],
                },
            )

        backend = LiveBackend(
            AppSettings(_env_file=None, openai_api_key="test"),
            httpx.AsyncClient(transport=httpx.MockTransport(respond)),
        )
        try:
            with pytest.raises(ProviderError, match="référence"):
                await backend.research(
                    "Ce document suffit-il ?",
                    "Projet",
                    {},
                    "web",
                    history=[
                        {
                            "role": "human",
                            "text": "Correction : ABC désigne mon document.",
                        }
                    ],
                )
        finally:
            await backend.close()

    asyncio.run(scenario())
