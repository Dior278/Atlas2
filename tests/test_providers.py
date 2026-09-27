import asyncio
import json

import httpx
import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from aparte.providers import LiveBackend, ProviderError
from aparte.settings import AppSettings
from aparte.workspace.api import app as api_module


def test_research_request_schema_and_retrieved_citations():
    requests = []

    def respond(request):
        payload = json.loads(request.content)
        requests.append(payload)
        if (
            payload.get("text", {}).get("format", {}).get("name")
            == "contextual_research_answer"
        ):
            content = {
                "type": "output_text",
                "text": json.dumps(
                    {
                        "points": [
                            {
                                "text": "Résultat sourcé.",
                                "source_ids": [0],
                                "time_basis": "not_applicable",
                            }
                        ],
                        "uncertainty": "",
                        "follow_up": "",
                    }
                ),
            }
        else:
            content = {
                "type": "output_text",
                "text": "Résultat sourcé.",
                "annotations": [
                    {
                        "type": "url_citation",
                        "title": "Source primaire",
                        "url": "https://example.org/paper",
                    }
                ],
            }
        return httpx.Response(
            200,
            json={
                "status": "completed",
                "output": [{"type": "message", "content": [content]}],
            },
        )

    async def scenario():
        backend = LiveBackend(
            AppSettings(_env_file=None, openai_api_key="test-secret"),
            httpx.AsyncClient(transport=httpx.MockTransport(respond)),
        )
        finding = await backend.research("Recherche", "robotique", {}, "web")
        assert finding.sources[0].url == "https://example.org/paper"
        assert len(requests) == 2
        assert all(request["store"] is False for request in requests)
        assert all(request["model"] == "gpt-5-mini" for request in requests)
        assert requests[0]["tools"] == [{"type": "web_search"}]
        assert requests[0]["reasoning"] == {"effort": "low"}
        assert requests[1]["text"]["format"]["strict"] is True
        assert requests[1]["text"]["format"]["name"] == "contextual_research_answer"
        assert requests[1]["reasoning"] == {"effort": "minimal"}
        await backend.close()

    asyncio.run(scenario())


def test_provider_failure_is_redacted_and_never_replaced_by_demo_data():
    async def scenario():
        client = httpx.AsyncClient(
            transport=httpx.MockTransport(
                lambda request: httpx.Response(401, text="leaked-secret")
            )
        )
        backend = LiveBackend(
            AppSettings(_env_file=None, openai_api_key="test-secret"), client
        )
        with pytest.raises(ProviderError, match="HTTP 401") as error:
            await backend.research("Question", "projet", {}, "web")
        assert "leaked-secret" not in str(error.value)
        await backend.close()

    asyncio.run(scenario())


@pytest.mark.parametrize("domain", ["https://dust.tt", "https://eu.dust.tt"])
def test_dust_stream_returns_source_references(domain):
    def respond(request):
        assert request.method == "GET"
        assert str(request.url).startswith(domain + "/api/v1/w/workspace/search?")
        assert request.headers["Authorization"] == "Bearer test-secret"
        assert request.url.params["includeTools"] == "false"
        assert request.url.params["viewType"] == "document"
        return httpx.Response(
            200,
            text='data: {"knowledgeResults":{"nodes":[{"title":"Note interne","sourceUrl":"https://example.org/doc"}]}}\n\n',
            headers={"Content-Type": "text/event-stream"},
        )

    async def scenario():
        backend = LiveBackend(
            AppSettings(
                _env_file=None,
                dust_api_key="test-secret",
                dust_workspace_id="workspace",
                dust_domain=domain,
            ),
            httpx.AsyncClient(transport=httpx.MockTransport(respond)),
        )
        result = await backend.dust_search("Projet")
        assert result.sources[0].title == "Note interne"
        assert "contenu intégral non fourni" in result.sources[0].excerpt
        await backend.close()

    asyncio.run(scenario())


@pytest.mark.parametrize("domain", ["eu.dust.tt", "https://eu.dust.tt/"])
def test_dust_domain_accepts_official_eu_origin(domain):
    assert (
        AppSettings(_env_file=None, dust_domain=domain).dust_domain
        == "https://eu.dust.tt"
    )


@pytest.mark.parametrize(
    "domain",
    ["http://eu.dust.tt", "https://dust.tt.example.org", "https://eu.dust.tt/api/v1"],
)
def test_dust_domain_rejects_wrong_or_insecure_destination(domain):
    with pytest.raises(ValueError, match="DUST_DOMAIN"):
        AppSettings(_env_file=None, dust_domain=domain)


@pytest.mark.parametrize("body", ['data: {"error":"failure"}\n\n', ": keepalive\n\n"])
def test_dust_does_not_treat_empty_or_failed_stream_as_success(body):
    async def scenario():
        backend = LiveBackend(
            AppSettings(
                _env_file=None, dust_api_key="test", dust_workspace_id="workspace"
            ),
            httpx.AsyncClient(
                transport=httpx.MockTransport(lambda _r: httpx.Response(200, text=body))
            ),
        )
        try:
            with pytest.raises(ProviderError):
                await backend.dust_search("Test")
        finally:
            await backend.close()

    asyncio.run(scenario())


def test_web_configuration_does_not_expose_credentials(monkeypatch, tmp_path):
    monkeypatch.setenv("APARTE_DATABASE_PATH", str(tmp_path / "api.sqlite3"))
    from aparte.workspace.api import app as api_module

    monkeypatch.setattr(
        api_module,
        "AppSettings",
        lambda: AppSettings(_env_file=None, openai_api_key="private-token"),
    )
    with TestClient(api_module.create_app()) as client:
        response = client.get("/v1/bootstrap")
        assert response.status_code == 200
        assert "private-token" not in response.text
        assert "openai_api_key" not in response.text
        assert client.get("/").status_code == 200
        assert client.get("/.env").status_code == 404
        assert client.get("/.Secrets").status_code == 404


def test_websocket_origin_validation_and_authenticated_unified_session(
    monkeypatch, tmp_path
):
    monkeypatch.setenv("APARTE_DATABASE_PATH", str(tmp_path / "api.sqlite3"))
    with TestClient(api_module.create_app()) as client:
        with pytest.raises(WebSocketDisconnect):
            with client.websocket_connect(
                "/v1/live", headers={"origin": "https://untrusted.example"}
            ):
                pass
        with client.websocket_connect(
            "/v1/live", headers={"origin": "http://testserver"}
        ) as ws:
            ws.send_json(
                {
                    "type": "client.hello",
                    "protocol_version": 12,
                    "client_id": "test",
                    "access_token": "wrong",
                }
            )
            with pytest.raises(WebSocketDisconnect):
                ws.receive_json()
        token = client.get("/v1/bootstrap").json()["access_token"]
        with client.websocket_connect(
            "/v1/live", headers={"origin": "http://testserver"}
        ) as ws:
            ws.send_json(
                {
                    "type": "client.hello",
                    "protocol_version": 12,
                    "client_id": "test",
                    "access_token": token,
                }
            )
            assert ws.receive_json()["type"] == "backend.hello"
        assert client.get("/v1/sessions/unknown/export").status_code == 403
