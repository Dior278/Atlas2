from __future__ import annotations

import asyncio
import os
import secrets
from contextlib import asynccontextmanager, suppress
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from fastapi import (
    FastAPI,
    HTTPException,
    Request,
    Response,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import TypeAdapter, ValidationError

from aparte.minutes import Review, calendar_export, markdown_export
from aparte.providers import LiveBackend
from aparte.settings import AppSettings
from aparte.workspace.adapters.exa import ExaSearch
from aparte.workspace.adapters.gradium import GradiumSTT, GradiumTTS
from aparte.workspace.adapters.jinko import JinkoFlights
from aparte.workspace.adapters.openai_stt import OpenAISTT
from aparte.workspace.adapters.openai_tts import OpenAITTS
from aparte.workspace.adapters.sqlite import SQLiteStore
from aparte.workspace.adapters.stt_registry import STTRegistry
from aparte.workspace.adapters.tts_registry import TTSRegistry
from aparte.workspace.adapters.typesafe import TypeSafeDecision
from aparte.workspace.config import AppConfig, ProductConfig, load_config, load_product
from aparte.workspace.core.coordinator import Coordinator
from aparte.workspace.core.engine import AtlasEngine
from aparte.workspace.core.models import SessionStatus, now_iso
from aparte.workspace.core.speaker import SpeakerAgent
from aparte.workspace.core.tools import ToolRegistry, ToolSpec
from aparte.workspace.integrations import register_research
from aparte.workspace.llm import OpenAICompatibleGenerator
from aparte.workspace.runtime import SemanticDecision, WorkspaceEngine

from .hub import WebSocketHub
from .schemas import (
    BackendHello,
    BoardCurate,
    BootstrapResponse,
    ClientHello,
    ClientMessage,
    FloorChanged,
    PlaybackChanged,
    ProtocolDocument,
    SessionCommand,
    SessionLanguage,
    SessionOpen,
    SessionRenameRequest,
    SessionStart,
    TaskCancel,
    TranscriptInject,
    VoiceModeCommand,
)

CLIENT_ADAPTER: TypeAdapter[ClientMessage] = TypeAdapter(ClientMessage)
LOCAL_HOSTS = {"127.0.0.1", "localhost", "testserver", "::1"}


def create_app() -> FastAPI:
    config, product = load_config(), load_product()
    hub = WebSocketHub()
    access_token = secrets.token_urlsafe(32)
    resources: Resources
    control_lock = asyncio.Lock()
    controller: WebSocket | None = None
    controller_id: str | None = None

    @asynccontextmanager
    async def lifespan(application):
        nonlocal resources
        resources = compose(product, config, hub)
        application.state.resources = resources
        await resources.engine.start()
        try:
            yield
        finally:
            await resources.engine.stop()
            await resources.exa.close()
            await resources.jinko.close()
            await resources.engine.backend.close()

    app = FastAPI(title=product.display_name, version="0.4.0", lifespan=lifespan)
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=list(LOCAL_HOSTS))

    @app.middleware("http")
    async def authorize(request: Request, call_next):
        origin = request.headers.get("origin")
        if (
            origin and urlsplit(origin).netloc != request.headers.get("host")
        ) or request.headers.get("sec-fetch-site") == "cross-site":
            return Response(status_code=403)
        if request.url.path.startswith("/v1/") and request.url.path not in {
            "/v1/bootstrap",
            "/v1/protocol",
        }:
            supplied = request.headers.get("authorization", "").removeprefix("Bearer ")
            if not secrets.compare_digest(supplied, access_token):
                return Response(status_code=403)
        response = await call_next(request)
        response.headers.update(
            {
                "Cache-Control": "no-store",
                "X-Content-Type-Options": "nosniff",
                "Referrer-Policy": "no-referrer",
            }
        )
        return response

    @app.get("/health")
    async def health():
        return {"status": "ok", "process": resources.engine.state.process_status}

    @app.get("/v1/bootstrap", response_model=BootstrapResponse)
    async def bootstrap(request: Request):
        if request.client.host not in {"127.0.0.1", "::1", "testclient"}:
            raise HTTPException(403, "Ouvrez Atlas sur cet ordinateur.")
        return BootstrapResponse(
            **product.model_dump(),
            active_model=config.llm.active_model,
            models=[item.id for item in config.llm.models],
            access_token=access_token,
            state=resources.engine.client_state(),
            sessions=await resources.engine.list_sessions(),
        )

    @app.get("/v1/protocol", response_model=ProtocolDocument)
    async def protocol_document():
        return ProtocolDocument(
            client=ClientHello(
                type="client.hello",
                protocol_version=product.protocol_version,
                client_id="example",
            ),
            server=BackendHello(
                type="backend.hello",
                project_id=product.project_id,
                protocol_version=product.protocol_version,
            ),
        )

    @app.patch("/v1/sessions/{session_id}")
    async def rename(session_id: str, body: SessionRenameRequest):
        if not await resources.engine.rename_session(session_id, body.title):
            raise HTTPException(404, "Session introuvable.")
        return {"updated": True}

    @app.delete("/v1/sessions/{session_id}", status_code=204)
    async def delete(session_id: str):
        async with control_lock:
            if not await resources.engine.delete_session(session_id):
                raise HTTPException(404, "Session introuvable.")
        return Response(status_code=204)

    @app.get("/v1/sessions/{session_id}/export")
    async def export_session(session_id: str):
        content = await resources.engine.export_session(session_id)
        if content is None:
            raise HTTPException(404, "Session introuvable.")
        return Response(
            content,
            media_type="text/markdown",
            headers={"Content-Disposition": f'attachment; filename="{session_id}.md"'},
        )

    @app.get("/v1/sessions/{session_id}/journal")
    async def journal(session_id: str):
        if await resources.engine.store.load(session_id) is None:
            raise HTTPException(404, "Session introuvable.")
        return await resources.engine.store.journal(session_id)

    @app.post("/v1/minutes")
    async def generate_minutes():
        task = resources.engine._spawn(resources.engine.generate_minutes())
        try:
            return await task
        except asyncio.CancelledError:
            raise HTTPException(409, "Analyse interrompue à la mise en pause.")
        except ValueError as error:
            raise HTTPException(409, str(error)) from error
        except Exception as error:
            raise HTTPException(502, "La préparation a échoué. Réessayez.") from error

    @app.patch("/v1/minutes")
    async def review_minutes(body: Review):
        try:
            return await resources.engine.review_minutes(body)
        except ValueError as error:
            raise HTTPException(409, str(error)) from error

    @app.get("/v1/sessions/{session_id}/minutes/{format}")
    async def export_minutes(session_id: str, format: str):
        state = await resources.engine.store.load(session_id)
        if state is None or not state.minutes or format not in {"md", "ics"}:
            raise HTTPException(404, "Engagements introuvables.")
        if format == "ics" and state.minutes.get("stale"):
            raise HTTPException(
                409, "Actualisez les engagements avant l’export calendrier."
            )
        content = (
            calendar_export(state.minutes, session_id)
            if format == "ics"
            else markdown_export(state.minutes, state.title)
        )
        return Response(
            content,
            media_type="text/calendar" if format == "ics" else "text/markdown",
            headers={
                "Content-Disposition": f'attachment; filename="{session_id}.{format}"'
            },
        )

    @app.websocket("/v1/live")
    async def live(websocket: WebSocket):
        nonlocal controller, controller_id
        origin = urlsplit(websocket.headers.get("origin", ""))
        if origin.scheme not in {
            "http",
            "https",
        } or origin.netloc != websocket.headers.get("host"):
            await websocket.close(code=1008)
            return
        await websocket.accept()
        joined = False
        try:
            hello = CLIENT_ADAPTER.validate_python(
                await asyncio.wait_for(websocket.receive_json(), 10)
            )
            if not isinstance(hello, ClientHello) or not secrets.compare_digest(
                hello.access_token, access_token
            ):
                await websocket.close(code=1008)
                return
            if hello.protocol_version != product.protocol_version:
                raise ValueError("Rechargez la page pour utiliser la nouvelle version.")
            async with control_lock:
                if controller is not None and controller_id != hello.client_id:
                    raise ValueError(
                        "Atlas est déjà ouvert dans un autre onglet. Fermez-le puis réessayez."
                    )
                if controller is not None:
                    # A reconnect from the same tab can replace a half-open socket.
                    # The old handler must never pause or command its replacement.
                    hub.disconnect(controller)
                    with suppress(Exception):
                        await asyncio.wait_for(controller.close(code=4000), timeout=1)
                    await resources.engine.client_disconnected()
                controller, controller_id = websocket, hello.client_id
                hub.attach(websocket)
                joined = True
                await websocket.send_json(
                    {
                        "type": "backend.hello",
                        "project_id": product.project_id,
                        "protocol_version": product.protocol_version,
                    }
                )
                await resources.engine._broadcast_state()
            while True:
                frame = await websocket.receive()
                if (
                    frame["type"] == "websocket.disconnect"
                    or controller is not websocket
                ):
                    break
                try:
                    if frame.get("bytes") is not None:
                        await resources.engine.ingest_audio(frame["bytes"])
                        continue
                    raw = frame.get("text", "")
                    if len(raw) > 64000:
                        raise ValueError("Message trop volumineux.")
                    message = CLIENT_ADAPTER.validate_json(raw)
                    if isinstance(message, BoardCurate):
                        if not resources.engine.state.consent_at:
                            raise ValueError(
                                "Reprenez la session avant d’organiser le tableau."
                            )
                        resources.engine._spawn(resources.engine.curate_board())
                    else:
                        async with control_lock:
                            if controller is not websocket:
                                break
                            await dispatch_client_message(resources.engine, message)
                except (ValueError, ValidationError) as error:
                    await websocket.send_json(
                        {
                            "type": "protocol.error",
                            "code": "COMMAND_REJECTED",
                            "message": "Vérifiez les champs envoyés."
                            if isinstance(error, ValidationError)
                            else str(error),
                        }
                    )
                except Exception:
                    await websocket.send_json(
                        {
                            "type": "protocol.error",
                            "code": "COMMAND_FAILED",
                            "message": "Cette opération a échoué. Vos données restent disponibles.",
                        }
                    )
        except (WebSocketDisconnect, RuntimeError, TimeoutError):
            pass
        except (ValueError, ValidationError) as error:
            await websocket.send_json(
                {
                    "type": "protocol.error",
                    "code": "CONNECTION_REJECTED",
                    "message": str(error)
                    if not isinstance(error, ValidationError)
                    else "Connexion invalide.",
                }
            )
            await websocket.close(code=1008)
        finally:
            if joined:
                async with control_lock:
                    hub.disconnect(websocket)
                    if controller is websocket:
                        try:
                            await resources.engine.client_disconnected()
                        finally:
                            controller = controller_id = None

    frontend = Path(
        os.environ.get(
            "APARTE_FRONTEND_DIR",
            Path(__file__).resolve().parents[4] / "frontend" / "dist",
        )
    )
    if (frontend / "index.html").is_file():
        app.mount("/", StaticFiles(directory=frontend, html=True), name="interface")
    return app


class Resources:
    def __init__(
        self, engine: AtlasEngine, exa: ExaSearch, jinko: JinkoFlights
    ) -> None:
        self.engine = engine
        self.exa = exa
        self.jinko = jinko


def compose(product: ProductConfig, config: AppConfig, hub: WebSocketHub) -> Resources:
    generator = OpenAICompatibleGenerator(config.llm)
    decision = SemanticDecision(TypeSafeDecision(config.decision), generator)
    backend = LiveBackend(AppSettings())
    stt_providers = {
        provider.id: GradiumSTT(provider)
        if provider.provider == "gradium"
        else OpenAISTT(provider)
        for provider in config.voice.stt.providers
    }
    stt = STTRegistry(config.voice.stt, stt_providers)
    tts_providers = {
        provider.id: GradiumTTS(provider)
        if provider.provider == "gradium"
        else OpenAITTS(provider)
        for provider in config.voice.tts.providers
    }
    tts = TTSRegistry(config.voice.tts, tts_providers)
    exa = ExaSearch(config.tools.exa)
    jinko = JinkoFlights(config.tools.jinko)
    tools = ToolRegistry(config.policy.research_max_concurrency)
    if exa.available:
        tools.register(
            ToolSpec(
                name="exa_search",
                description="Search the current web and return titles, URLs, dates, and relevant highlights.",
                effect="read",
                input_schema={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"},
                        "num_results": {"type": "integer", "minimum": 1, "maximum": 10},
                    },
                    "required": ["query"],
                },
                handler=exa.search,
            )
        )
    if jinko.available:
        tools.register(
            ToolSpec(
                name="jinko_flight_calendar",
                description="Search read-only flight calendar availability for explicit airports and a date.",
                effect="read",
                input_schema={
                    "type": "object",
                    "properties": {
                        "origins": {"type": "array", "items": {"type": "string"}},
                        "destinations": {"type": "array", "items": {"type": "string"}},
                        "departure_date": {"type": "string"},
                        "currency": {"type": "string"},
                    },
                    "required": ["origins", "destinations", "departure_date"],
                },
                handler=jinko.flight_calendar,
            )
        )

    async def list_capabilities(_arguments: dict[str, Any]) -> dict[str, Any]:
        return {
            "status": "ok",
            "capabilities": tools.prompt_catalog(),
            "message": (
                "These are the capabilities currently registered and available to Atlas."
            ),
        }

    tools.register(
        ToolSpec(
            name="system_capabilities",
            description=(
                "List Atlas's currently registered tools and their effects. Use this when the room asks "
                "what Atlas can do, which tools are available, or whether a capability exists."
            ),
            effect="read",
            input_schema={"type": "object", "properties": {}},
            handler=list_capabilities,
        )
    )
    research_health = register_research(tools, backend)
    coordinator = Coordinator(generator, tools, config.policy, config.llm.roles)
    speaker = SpeakerAgent(generator, config.llm.roles.speaker)
    store = SQLiteStore(config.storage.resolved_path())
    engine = WorkspaceEngine(
        backend=backend,
        product=product,
        config=config,
        store=store,
        decision=decision,
        speaker=speaker,
        coordinator=coordinator,
        stt=stt,
        tts=tts,
        publish=hub.broadcast,
        tool_health={"exa": exa.available, "jinko": jinko.available, **research_health},
    )
    return Resources(engine, exa, jinko)


async def dispatch_client_message(engine: AtlasEngine, message: ClientMessage) -> None:
    if isinstance(message, SessionStart):
        await engine.start_session(message.model_dump(mode="json", exclude={"type"}))
    elif isinstance(message, SessionOpen):
        if not await engine.open_session(message.session_id):
            raise ValueError("Session introuvable.")
    elif isinstance(message, SessionLanguage):
        await engine.set_language(message.language)
    elif isinstance(message, VoiceModeCommand):
        await engine.set_voice_mode(message.mode)
    elif isinstance(message, BoardCurate):
        await engine.curate_board()
    elif isinstance(message, TaskCancel):
        await engine.cancel_mission(message.task_id)
    elif isinstance(message, SessionCommand):
        if message.command == "resume":
            if message.consent is not True:
                raise ValueError("Confirmez l’accord avant de reprendre.")
            engine.state.consent_at = now_iso()
        await engine.session_command(message.command)
    elif isinstance(message, FloorChanged):
        await engine.floor_changed(message.busy)
    elif isinstance(message, TranscriptInject):
        if engine.state.session_status != SessionStatus.LISTENING:
            raise ValueError("Reprenez la session avant d’envoyer un message.")
        await engine.commit_utterance(message.text, source="manual")
    elif isinstance(message, PlaybackChanged):
        await engine.playback_changed(message.speech_id, message.type.split(".", 1)[1])
    else:
        return
