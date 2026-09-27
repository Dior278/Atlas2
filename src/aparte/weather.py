"""Read-only, timestamped weather lookup; never guess a region's representative city."""

import json
from datetime import date
from typing import Literal

import httpx
from pydantic import BaseModel, ConfigDict, Field

from .models import Finding, Source


class WeatherQuery(BaseModel):
    model_config = ConfigDict(extra="forbid")
    location: str = Field(min_length=2, max_length=150)
    country_code: str = Field(default="", pattern=r"^(?:[A-Z]{2})?$")
    date: str = ""
    period: Literal["current", "forecast"] = "current"


CONDITIONS = {
    0: "ciel dégagé",
    1: "ciel peu nuageux",
    2: "ciel partiellement nuageux",
    3: "ciel couvert",
    45: "brouillard",
    48: "brouillard givrant",
    51: "bruine légère",
    53: "bruine",
    55: "bruine dense",
    61: "pluie faible",
    63: "pluie modérée",
    65: "forte pluie",
    66: "pluie verglaçante",
    67: "pluie verglaçante",
    71: "neige faible",
    73: "neige",
    75: "forte neige",
    77: "grains de neige",
    80: "averses faibles",
    81: "averses",
    82: "fortes averses",
    85: "averses de neige",
    86: "fortes averses de neige",
    95: "orage",
    96: "orage avec grêle",
    99: "orage avec grêle",
}


async def lookup_weather(client: httpx.AsyncClient, query: str) -> Finding:
    from .providers import ProviderError, normalize

    try:
        request = WeatherQuery.model_validate_json(query)
        if request.date:
            date.fromisoformat(request.date)
    except ValueError as exc:
        raise ProviderError(
            "Météo : la ville et la date doivent être précisées avant la recherche."
        ) from exc
    params = {"name": request.location, "count": 5, "language": "fr", "format": "json"}
    if request.country_code:
        params["countryCode"] = request.country_code
    try:
        response = await client.get(
            "https://geocoding-api.open-meteo.com/v1/search", params=params, timeout=12
        )
        response.raise_for_status()
        places = response.json().get("results", [])
        exact = [
            p for p in places if normalize(p["name"]) == normalize(request.location)
        ]
        if exact:
            places = exact
        # Countries/regions have coordinates too: those are not national weather.
        # Reject their feature class instead of turning the centroid into a city.
        if any(not p.get("feature_code", "").startswith("PPL") for p in places):
            return Finding(
                summary="La recherche ne désigne pas une ville de façon certaine. Les conditions varient selon les lieux : quelle ville souhaites-tu vérifier ?"
            )
        if request.country_code:
            places = [
                p for p in places if p.get("country_code") == request.country_code
            ]
        # Search also returns small homonymous localities. With an explicit country,
        # prefer an unambiguous major city; keep asking for genuinely comparable places.
        ranked = sorted(places, key=lambda p: p.get("population", 0), reverse=True)
        if (
            request.country_code
            and len(ranked) > 1
            and ranked[0].get("population", 0)
            >= max(100000, 20 * ranked[1].get("population", 0))
        ):
            places = ranked[:1]
        if not places:
            return Finding(
                summary=f"Je n'ai pas identifié « {request.location} ». Peux-tu préciser la ville et le pays ?"
            )
        distinct = {(p.get("country_code"), p.get("admin1")) for p in places}
        if len(distinct) > 1:
            choices = "; ".join(
                dict.fromkeys(
                    f"{p['name']}, {p.get('admin1', p.get('country', ''))}"
                    for p in places[:3]
                )
            )
            return Finding(
                summary=f"Plusieurs lieux correspondent : {choices}. Lequel veux-tu ?"
            )
        place = places[0]
        response = await client.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": place["latitude"],
                "longitude": place["longitude"],
                "timezone": "auto",
                "current": "temperature_2m,apparent_temperature,weather_code,wind_speed_10m",
                "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max",
                "forecast_days": 7,
            },
            timeout=12,
        )
        response.raise_for_status()
        data = response.json()
        current = data["current"]
        local_day = current["time"][:10]
        target = request.date or local_day
        date.fromisoformat(target)
        name = ", ".join(
            filter(None, (place["name"], place.get("admin1"), place.get("country")))
        )
        if request.period == "current" and target == local_day:
            if any(
                current.get(k) is None
                for k in (
                    "weather_code",
                    "temperature_2m",
                    "apparent_temperature",
                    "wind_speed_10m",
                )
            ):
                raise ValueError("Missing weather measurements")
            sky = CONDITIONS.get(current["weather_code"], "conditions variables")
            summary = (
                f"D'après Open-Meteo, à {name}, les conditions estimées à {current['time'][11:16]}, heure locale, "
                f"sont : {sky}, {current['temperature_2m']} degrés, avec un ressenti de {current['apparent_temperature']} degrés "
                f"et un vent de {current['wind_speed_10m']} kilomètres par heure."
            )
        else:
            daily = data["daily"]
            if target not in daily["time"]:
                return Finding(
                    summary="Cette date est hors de la prévision à sept jours disponible. Pour quelle date proche veux-tu la météo ?"
                )
            index = daily["time"].index(target)
            if any(
                daily[k][index] is None
                for k in (
                    "weather_code",
                    "temperature_2m_min",
                    "temperature_2m_max",
                    "precipitation_probability_max",
                )
            ):
                raise ValueError("Missing forecast")
            sky = CONDITIONS.get(daily["weather_code"][index], "conditions variables")
            summary = (
                f"D'après Open-Meteo, pour {name} le {date.fromisoformat(target).strftime('%d/%m/%Y')}, la prévision indique "
                f"{sky}, de {daily['temperature_2m_min'][index]} à {daily['temperature_2m_max'][index]} degrés, "
                f"avec un risque maximal de précipitations de {daily['precipitation_probability_max'][index]} pour cent."
            )
        return Finding(
            summary=summary,
            sources=[
                Source(
                    title="Open-Meteo · prévision et conditions estimées",
                    url="https://open-meteo.com/",
                    excerpt=json.dumps(
                        {
                            "location": name,
                            "local_time": current["time"],
                            "timezone": data.get("timezone"),
                            "date": target,
                        },
                        ensure_ascii=False,
                    ),
                )
            ],
        )
    except (httpx.HTTPError, ValueError, KeyError, TypeError, IndexError) as exc:
        raise ProviderError(
            "Météo : les données actualisées sont momentanément indisponibles. Je ne peux pas confirmer les conditions."
        ) from exc
