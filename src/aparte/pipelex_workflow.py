"""A real two-step Pipelex method, executed through the official hosted SDK."""

from pathlib import Path

from pipelex_sdk.client import PipelexAPIClient
from pipelex_sdk.runs import WaitForResultOptions

from .models import Finding, Source
from .providers import ProviderError

METHOD = Path(__file__).parent / "data" / "compare.mthds"


async def compare_options(context: str, api_key: str) -> Finding:
    if not api_key:
        raise ProviderError(
            "Pipelex : renseignez PIPELEX_API_KEY pour comparer les options."
        )
    try:
        async with PipelexAPIClient(
            api_key=api_key,
            base_url="https://api.pipelex.com",
            request_timeout_seconds=30,
        ) as client:
            result = await client.start_and_wait(
                mthds_contents=[METHOD.read_text(encoding="utf-8")],
                inputs={"context": context},
                wait_options=WaitForResultOptions(
                    interval_seconds=2, timeout_seconds=90
                ),
            )
            # start_and_wait returns RunResults only after successful completion.
            content = result.main_stuff
            text = content.get("text", "") if isinstance(content, dict) else ""
            if not text.strip():
                raise ProviderError(
                    "Pipelex : le workflow n'a pas retourné de comparaison."
                )
            return Finding(
                summary=text,
                sources=[
                    Source(
                        title="Comparaison Pipelex",
                        excerpt=f"Exécution réelle : {result.pipeline_run_id}. Basée sur la discussion ; ce workflow n'effectue pas de recherche web.",
                    )
                ],
            )
    except ProviderError:
        raise
    except Exception as exc:
        code = getattr(exc, "status_code", None)
        suffix = f" (HTTP {code})" if isinstance(code, int) else ""
        raise ProviderError(
            f"Pipelex : exécution indisponible{suffix}. Vérifiez l'accès API et les crédits."
        ) from exc
