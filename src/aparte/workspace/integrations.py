"""Aparté research providers registered in the single meeting engine."""

from aparte.workspace.core.tools import ToolSpec


def register_research(registry, backend):
    settings = backend.settings
    available = {
        "web": bool(settings.openai_token),
        "weather": True,
        "dust": bool(
            settings.key("dust_api_key") and settings.key("dust_workspace_id")
        ),
        "pipelex": bool(settings.key("pipelex_api_key")),
    }
    descriptions = {
        "web": "Recherche web actuelle avec sources citées. Utiliser pour vérifier des informations externes.",
        "weather": "Prévisions météo réelles pour un lieu et une date explicites, via Open-Meteo.",
        "dust": "Recherche dans les documents internes autorisés du workspace Dust.",
        "pipelex": "Compare des options à partir du dossier explicite fourni. Aucun achat ni réservation.",
    }
    for provider, configured in available.items():
        if not configured:
            continue

        async def run(arguments, provider=provider):
            query = arguments.get("query")
            if not isinstance(query, str) or not 1 <= len(query.strip()) <= 12000:
                raise ValueError("query doit contenir entre 1 et 12 000 caractères")
            finding = await backend.research(query, "workspace", {}, provider)
            return {
                "status": "ok",
                "summary": finding.summary,
                "results": [s.model_dump(mode="json") for s in finding.sources],
            }

        registry.register(
            ToolSpec(
                name=f"research_{provider}",
                description=descriptions[provider],
                effect="read",
                input_schema={
                    "type": "object",
                    "properties": {"query": {"type": "string", "maxLength": 12000}},
                    "required": ["query"],
                    "additionalProperties": False,
                },
                handler=run,
            )
        )
    return available
