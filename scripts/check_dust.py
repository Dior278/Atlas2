"""Read-only Dust connection test. Never print credentials or document contents."""

import asyncio
import json

import httpx

from aparte.providers import LiveBackend, ProviderError
from aparte.settings import AppSettings


async def main():
    settings = AppSettings()
    statuses = []
    diagnostic = {}
    response_types = []

    async def response_received(response):
        statuses.append(response.status_code)
        response_types.append(response.headers.get("content-type", ""))
        if response.is_error:
            await response.aread()
            try:
                error = response.json().get("error", {})
                if isinstance(error, dict):
                    for field in ("type", "message"):
                        value = str(error.get(field, ""))
                        for name in ("dust_api_key", "dust_workspace_id"):
                            secret = settings.key(name)
                            if secret:
                                value = value.replace(secret, "[redacted]")
                        diagnostic[field] = value[:500]
            except ValueError:
                pass

    backend = LiveBackend(
        settings,
        httpx.AsyncClient(
            timeout=30,
            follow_redirects=False,
            event_hooks={"response": [response_received]},
        ),
    )
    result = {"domain": settings.dust_domain}
    try:
        finding = await backend.dust_search("test de connexion")
        result.update(success=True, references_found=len(finding.sources))
    except ProviderError as exc:
        result.update(success=False, error=str(exc))
    finally:
        await backend.close()
    result["http_statuses"] = statuses
    result["response_types"] = response_types
    if diagnostic:
        result["provider_diagnostic"] = diagnostic
    print(json.dumps(result, ensure_ascii=True))
    return result["success"]


if __name__ == "__main__":
    raise SystemExit(0 if asyncio.run(main()) else 1)
