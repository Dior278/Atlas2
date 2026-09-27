import asyncio
import json

import pytest

from aparte.models import Finding, Source
from aparte.providers import LiveBackend, ProviderError
from aparte.research_answer import compose_research_answer


@pytest.mark.parametrize("source_ids", [[-1], [1], []])
def test_synthesis_cannot_cite_missing_sources(source_ids):
    async def scenario():
        class Backend:
            output_text = staticmethod(LiveBackend.output_text)

            async def _research_response(self, payload):
                context = json.loads(payload["input"])
                assert (
                    context["request"]["conversation"][-1]["text"]
                    == "Correction explicite"
                )
                return {
                    "output": [
                        {
                            "type": "message",
                            "content": [
                                {
                                    "type": "output_text",
                                    "text": json.dumps(
                                        {
                                            "points": [
                                                {
                                                    "text": "Affirmation",
                                                    "source_ids": source_ids,
                                                    "time_basis": "not_applicable",
                                                }
                                            ],
                                            "uncertainty": "",
                                            "follow_up": "",
                                        }
                                    ),
                                }
                            ],
                        }
                    ]
                }

        with pytest.raises(ProviderError, match="références"):
            await compose_research_answer(
                Backend(),
                {"conversation": [{"text": "Correction explicite"}]},
                Finding(
                    summary="Résultat brut",
                    sources=[Source(title="Source", url="https://example.org")],
                ),
            )

    asyncio.run(scenario())


def test_unknown_conditions_precede_claim_and_typical_data_is_labeled():
    async def scenario():
        class Backend:
            output_text = staticmethod(LiveBackend.output_text)

            async def _research_response(self, _payload):
                return {
                    "output": [
                        {
                            "type": "message",
                            "content": [
                                {
                                    "type": "output_text",
                                    "text": json.dumps(
                                        {
                                            "points": [
                                                {
                                                    "text": "La moyenne historique est de 20 degrés.",
                                                    "source_ids": [0],
                                                    "time_basis": "historical_or_typical",
                                                }
                                            ],
                                            "uncertainty": "La ville et les conditions actuelles restent inconnues.",
                                            "follow_up": "Dans quelle ville ?",
                                        }
                                    ),
                                }
                            ],
                        }
                    ]
                }

        result = await compose_research_answer(
            Backend(),
            {},
            Finding(
                summary="Moyennes historiques",
                sources=[
                    Source(title="Archive", url="https://example.org/archive"),
                    Source(title="Sans rapport", url="https://example.org/other"),
                ],
            ),
        )
        assert result.summary.startswith(
            "La ville et les conditions actuelles restent inconnues."
        )
        assert "pas une observation actuelle" in result.summary
        assert result.summary.endswith("Dans quelle ville ?")
        assert [s.title for s in result.sources] == ["Archive"]

    asyncio.run(scenario())
