import asyncio
import json

import httpx
import pytest

from aparte.providers import ProviderError
from aparte.weather import lookup_weather


def weather_payload():
    return {
        "timezone": "Europe/Paris",
        "current": {
            "time": "2026-09-26T12:15",
            "temperature_2m": 21.5,
            "apparent_temperature": 20,
            "wind_speed_10m": 12,
            "weather_code": 2,
        },
        "daily": {
            "time": ["2026-09-26", "2026-09-27"],
            "weather_code": [2, 61],
            "temperature_2m_min": [12, 13],
            "temperature_2m_max": [22, 19],
            "precipitation_probability_max": [10, 75],
        },
    }


@pytest.mark.parametrize(
    "period,target,expected",
    [
        ("current", "", "21.5 degrés"),
        ("forecast", "2026-09-27", "75 pour cent"),
        ("forecast", "2027-01-01", "hors de la prévision"),
    ],
)
def test_weather_uses_requested_place_and_provider_local_date(period, target, expected):
    async def scenario():
        def respond(request):
            if "geocoding" in request.url.host:
                assert request.url.params["name"] == "Bordeaux"
                assert request.url.params["countryCode"] == "FR"
                return httpx.Response(
                    200,
                    json={
                        "results": [
                            {
                                "name": "Bordeaux",
                                "feature_code": "PPL",
                                "country": "France",
                                "country_code": "FR",
                                "admin1": "Nouvelle-Aquitaine",
                                "latitude": 44.8,
                                "longitude": -0.5,
                                "population": 250000,
                            },
                            {
                                "name": "Bordeaux-en-Gâtinais",
                                "feature_code": "PPL",
                                "country_code": "FR",
                                "admin1": "Centre",
                                "population": 150,
                            },
                            {
                                "name": "Bordeaux",
                                "feature_code": "PPL",
                                "country_code": "FR",
                                "admin1": "Normandie",
                                "population": 100,
                            },
                        ]
                    },
                )
            assert request.url.params["latitude"] == "44.8"
            return httpx.Response(200, json=weather_payload())

        async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
            finding = await lookup_weather(
                client,
                json.dumps(
                    {
                        "location": "Bordeaux",
                        "country_code": "FR",
                        "date": target,
                        "period": period,
                    }
                ),
            )
            assert expected in finding.summary
            if finding.sources:
                assert "2026-09-26T12:15" in finding.sources[0].excerpt

    asyncio.run(scenario())


def test_ambiguous_city_does_not_fetch_forecast():
    async def scenario():
        def respond(request):
            assert "geocoding" in request.url.host
            return httpx.Response(
                200,
                json={
                    "results": [
                        {
                            "name": "Paris",
                            "feature_code": "PPL",
                            "country_code": "FR",
                            "country": "France",
                        },
                        {
                            "name": "Paris",
                            "feature_code": "PPL",
                            "country_code": "US",
                            "country": "États-Unis",
                        },
                    ]
                },
            )

        async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
            finding = await lookup_weather(client, '{"location":"Paris"}')
            assert "Lequel" in finding.summary
            assert not finding.sources

    asyncio.run(scenario())


def test_weather_failure_does_not_become_simulated_weather():
    async def scenario():
        async with httpx.AsyncClient(
            transport=httpx.MockTransport(lambda r: httpx.Response(503))
        ) as client:
            with pytest.raises(ProviderError, match="indisponibles"):
                await lookup_weather(client, '{"location":"Bordeaux"}')

    asyncio.run(scenario())


def test_weather_missing_measurement_is_not_spoken_as_a_value():
    async def scenario():
        def respond(request):
            if "geocoding" in request.url.host:
                return httpx.Response(
                    200,
                    json={
                        "results": [
                            {
                                "name": "Bordeaux",
                                "feature_code": "PPL",
                                "latitude": 44.8,
                                "longitude": -0.5,
                            }
                        ]
                    },
                )
            payload = weather_payload()
            payload["current"]["temperature_2m"] = None
            return httpx.Response(200, json=payload)

        async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
            with pytest.raises(ProviderError, match="indisponibles"):
                await lookup_weather(client, '{"location":"Bordeaux"}')

    asyncio.run(scenario())
