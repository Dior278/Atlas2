"""Atlas browser acceptance checks. Uses synthetic providers and an isolated DB."""

import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PORT = 8878
sys.path.insert(0, str(ROOT))


def serve():
    import asyncio
    from types import SimpleNamespace

    import uvicorn
    from tests.workspace.test_aparte import MinutesBackend, make_engine
    from tests.workspace.test_engine import FakeDecision, FakeGenerator

    from aparte.workspace.adapters.sqlite import SQLiteStore
    from aparte.workspace.api import app as api
    from aparte.workspace.core.models import LLMResult
    from aparte.workspace.core.tools import ToolSpec

    class SyntheticDecision(FakeDecision):
        async def evaluate(self, state, text):
            route = "investigate" if text.startswith("Atlas, recherche") else "capture"
            return await FakeDecision(route, initiative="proactive").evaluate(
                state, text
            )

    class SyntheticGenerator(FakeGenerator):
        async def generate(self, messages, model_id=None):
            system = messages[0]["content"]
            if "background missions" in system:
                if any("TOOL_RESULT" in m["content"] for m in messages):
                    value = {"working": "Résultat disponible", "tool": None}
                else:
                    latest = json.loads(messages[-1]["content"])["recent_transcript"][
                        -1
                    ]["text"]
                    value = {
                        "working": "Recherche de la documentation",
                        "tool": {
                            "name": "fake_search",
                            "arguments": {
                                "query": "lente" if "lente" in latest else "rapide"
                            },
                        },
                    }
                content = json.dumps(value)
            elif '"kind": "task_done"' in messages[-1]["content"]:
                content = json.dumps(
                    {
                        "speak": True,
                        "spoken_core": "La documentation de contrôle est disponible.",
                    }
                )
            elif "structured shared memory" in system:
                content = json.dumps(
                    {
                        "synthesis": [
                            "L’équipe prépare le prototype pour la démonstration."
                        ],
                        "topics": ["Une interface claire et accessible"],
                        "commitments": ["Renard prépare le prototype."],
                        "actions": ["Vérifier le parcours sur mobile."],
                    }
                )
            elif "Give this evolving session" in system:
                content = "Prototype de démonstration"
            elif "board" in system.lower():
                content = json.dumps(
                    {
                        "desired_cards": [
                            {
                                "kind": "idea",
                                "concept_key": "mobile",
                                "title": "Une interface lisible sur mobile",
                                "body": "Simplifier le parcours et garder les réglages secondaires accessibles dans un menu.",
                                "source_card_ids": [],
                            }
                        ],
                        "retirements": [],
                    }
                )
            else:
                return await super().generate(messages, model_id)
            return LLMResult(content=content, model="synthetic", provider="test")

    def compose(product, config, hub):
        engine, _ = make_engine(
            SQLiteStore(Path(os.environ["ATLAS_BROWSER_TEST_DATABASE"])),
            generator=SyntheticGenerator(),
            decision=SyntheticDecision(),
        )

        async def search(arguments):
            if arguments["query"] == "lente":
                await asyncio.Event().wait()
            return {
                "status": "ok",
                "summary": "Documentation de contrôle",
                "results": [
                    {
                        "title": "Source de contrôle",
                        "url": "https://example.org/atlas-evidence",
                    },
                ],
            }

        engine.coordinator.tools.register(
            ToolSpec(
                name="fake_search",
                description="Synthetic browser test",
                effect="read",
                input_schema={},
                handler=search,
            )
        )
        engine.publish = hub.broadcast
        return SimpleNamespace(
            engine=engine, exa=MinutesBackend(), jinko=MinutesBackend()
        )

    api.compose = compose
    uvicorn.run(api.create_app(), host="127.0.0.1", port=PORT, log_level="warning")


def check_tab_audio(playwright, base_url):
    """Capture actual tab output; needs full Chromium on Windows, not headless.

    No fake media device, external call, microphone or provider is used. This
    verifies browser tab capture, not delivery through Meet, Teams or Zoom.
    """
    from playwright.sync_api import expect

    browser = playwright.chromium.launch(
        headless=False,
        args=[
            "--window-position=-32000,-32000",
            "--auto-select-tab-capture-source-by-title=Atlas",
            "--autoplay-policy=no-user-gesture-required",
        ],
    )
    try:
        context = browser.new_context()
        atlas = context.new_page()
        atlas.goto(base_url)
        atlas.get_by_label("Source de la conversation").select_option("mixed")
        atlas.get_by_text("Faire entendre Atlas dans l’appel", exact=True).click()
        receiver = context.new_page()
        receiver.goto(f"{base_url}/health")
        receiver.set_content(
            '<title>Audio receiver</title><button id="capture">Capture</button>'
        )
        receiver.evaluate("""() => {
          document.querySelector('#capture').onclick = async () => {
            try {
              window.stream = await navigator.mediaDevices.getDisplayMedia({video:true, audio:true});
              window.tracks = stream.getAudioTracks().length;
              if (!window.tracks) throw Error('No audio track');
              window.ctx = new AudioContext();
              await ctx.resume();
              window.analyser = ctx.createAnalyser();
              ctx.createMediaStreamSource(stream).connect(analyser);
              window.peak = 0;
              window.timer = setInterval(() => {
                const data = new Float32Array(analyser.fftSize);
                analyser.getFloatTimeDomainData(data);
                window.peak = Math.max(window.peak,
                  Math.sqrt(data.reduce((sum,v) => sum+v*v,0)/data.length));
              }, 10);
              window.ready = true;
            } catch(e) {window.failure = String(e);}
          };
        }""")
        receiver.get_by_role("button", name="Capture", exact=True).click()
        receiver.wait_for_function("window.ready || window.failure", timeout=15000)
        assert receiver.evaluate("!!window.ready"), receiver.evaluate("window.failure")
        receiver.wait_for_timeout(300)
        baseline = receiver.evaluate("window.peak")
        atlas.get_by_role("button", name="Jouer le son de test").click()
        expect(atlas.get_by_role("status")).to_contain_text(
            "Un participant doit confirmer"
        )
        receiver.wait_for_function("window.peak > 0.02", timeout=5000)
        peak = receiver.evaluate("window.peak")
        assert baseline < 0.001, "The captured tab was not silent before the signal"
        result = {
            "actual_tab_capture": True,
            "baseline_rms": baseline,
            "signal_rms": peak,
            "external_meeting_tested": False,
        }
        (ROOT / "tmp/atlas-tab-audio-validation.json").write_text(
            json.dumps(result, indent=2), encoding="utf-8"
        )
        receiver.evaluate(
            "clearInterval(timer); stream.getTracks().forEach(t=>t.stop()); ctx.close();"
        )
        return result
    finally:
        browser.close()


def check(tab_audio=False):
    from playwright.sync_api import expect, sync_playwright

    widths = [320, 390, 768, 1440]
    (ROOT / "tmp").mkdir(exist_ok=True)
    logs = ROOT / "tmp" / "atlas-browser-server.log"
    with (
        tempfile.TemporaryDirectory(
            prefix="atlas-browser-", dir=ROOT / "tmp"
        ) as temporary,
        logs.open("w", encoding="utf-8") as log,
    ):
        process = subprocess.Popen(
            [
                sys.executable,
                str(Path(__file__).resolve()),
                "--serve",
            ],
            cwd=ROOT,
            env={
                **os.environ,
                "ATLAS_BROWSER_TEST_DATABASE": str(Path(temporary) / "test.sqlite3"),
            },
            stdout=log,
            stderr=log,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        try:
            for _ in range(100):
                if process.poll() is not None:
                    raise RuntimeError(
                        "Le serveur de test s’est arrêté. Voir tmp/atlas-browser-server.log."
                    )
                try:
                    urllib.request.urlopen(f"http://127.0.0.1:{PORT}/health", timeout=1)
                    break
                except OSError:
                    time.sleep(0.1)
            else:
                raise RuntimeError("The isolated server did not start")
            with sync_playwright() as p:
                audio_report = (
                    check_tab_audio(p, f"http://127.0.0.1:{PORT}")
                    if tab_audio
                    else None
                )
                browser = p.chromium.launch(
                    args=[
                        "--use-fake-ui-for-media-stream",
                        "--use-fake-device-for-media-stream",
                        "--autoplay-policy=no-user-gesture-required",
                    ]
                )
                context = browser.new_context(
                    viewport={"width": 1440, "height": 1000}, permissions=["microphone"]
                )
                page = context.new_page()
                page.add_init_script("""(() => {
                  const NativeSocket = window.WebSocket;
                  window.__testSockets = [];
                  window.WebSocket = class extends NativeSocket {
                    constructor(...args) { super(...args); window.__testSockets.push(this); }
                  };
                })();""")
                errors = []
                page.on("pageerror", lambda e: errors.append(str(e)))
                page.goto(f"http://127.0.0.1:{PORT}/")
                expect(
                    page.get_by_role("heading", name="Faites une place à Atlas.")
                ).to_be_visible()
                expect(
                    page.get_by_role("button", name="Démarrer une session")
                ).to_be_disabled()

                def responsive(label, screenshots=True):
                    for width in widths:
                        page.set_viewport_size({"width": width, "height": 900})
                        page.wait_for_timeout(100)
                        overflow = page.evaluate(
                            "document.documentElement.scrollWidth > innerWidth + 1"
                        )
                        assert not overflow, (
                            f"Horizontal overflow at {width}px in {label}"
                        )
                        if screenshots and width in {390, 1440}:
                            page.screenshot(
                                path=str(ROOT / "tmp" / f"atlas-{label}-{width}.png"),
                                full_page=True,
                            )

                responsive("home")
                page.get_by_label("Source de la conversation").select_option("mixed")
                page.get_by_text(
                    "Faire entendre Atlas dans l’appel", exact=True
                ).click()
                responsive("audio-appel")
                page.get_by_role("button", name="Jouer le son de test").click()
                expect(page.get_by_role("status")).to_contain_text(
                    "Un participant doit confirmer"
                )
                page.get_by_label("Source de la conversation").select_option("text")
                page.get_by_role("checkbox").check()
                expect(
                    page.get_by_role("button", name="Démarrer une session")
                ).to_be_enabled()
                page.get_by_role("button", name="Démarrer une session").click()
                field = page.get_by_role("textbox", name="Message à Atlas")
                expect(field).to_be_enabled()
                page.get_by_label("Options de la session").click()
                page.get_by_text(
                    "Faire entendre Atlas dans l’appel", exact=True
                ).click()
                responsive("audio-menu", screenshots=False)
                page.get_by_role("button", name="Jouer le son de test").click()
                expect(page.get_by_role("status")).to_contain_text(
                    "Un participant doit confirmer"
                )
                page.get_by_label("Options de la session").click()
                field.fill("Je préparerai le prototype pour la démonstration.")
                field.press("Enter")
                page.get_by_role("button", name="Notes", exact=True).click()
                expect(page.locator(".notes-document")).to_contain_text(
                    "prototype", timeout=15000
                )
                responsive("notes")

                page.get_by_label("Options de la session").click()
                page.get_by_title("Couper la voix").click()
                page.get_by_label("Options de la session").click()
                field.fill("Atlas, recherche lente pour tester l’annulation.")
                field.press("Enter")
                page.get_by_role("button", name="Agents", exact=True).click()
                page.locator('[data-node="worker"]').click()
                expect(
                    page.get_by_role("button", name="Arrêter cette recherche")
                ).to_be_visible()
                page.get_by_role("button", name="Arrêter cette recherche").click()
                expect(page.locator(".node-inspector")).to_contain_text("Annulée")
                responsive("recherche-annulee")
                page.get_by_label("Fermer les détails").click()
                field.fill("Atlas, recherche la documentation de contrôle.")
                field.press("Enter")
                page.get_by_role("button", name="Conversation", exact=True).click()
                expect(
                    page.get_by_text(
                        "La documentation de contrôle est disponible.", exact=True
                    )
                ).to_be_visible()
                page.get_by_text("Origine de cette réponse", exact=True).click()
                expect(
                    page.get_by_role("link", name="Source de contrôle")
                ).to_have_attribute("href", "https://example.org/atlas-evidence")
                responsive("reponse-sourcee")

                for view in ["Tableau", "Conversation", "Agents", "Engagements"]:
                    page.get_by_role("button", name=view, exact=True).click()
                    responsive(view.lower())
                page.get_by_role("button", name="Préparer les propositions").click()
                expect(page.locator(".commitment")).to_have_count(1)
                page.get_by_label("Responsable").select_option("renard")
                page.get_by_label("Échéance confirmée").fill("2026-10-02")
                page.get_by_role("button", name="Confirmer", exact=True).click()
                expect(page.locator(".commitment.confirmed")).to_have_count(1)
                with page.expect_download() as download:
                    page.get_by_role("button", name="Rappels calendrier").click()
                calendar = Path(download.value.path()).read_text(encoding="utf-8")
                assert "BEGIN:VEVENT" in calendar and "20261002" in calendar
                responsive("engagements-confirmes")

                field.fill("Finalement, nous décalons le prototype.")
                field.press("Enter")
                page.get_by_role("button", name="Engagements", exact=True).click()
                expect(page.locator(".notice")).to_contain_text("discussion a évolué")
                expect(
                    page.get_by_role("button", name="Confirmer", exact=True)
                ).to_be_disabled()
                page.get_by_title("Mettre en pause").click()
                expect(field).to_be_disabled()
                page.get_by_title("Reprendre l’assistant").click()
                dialog = page.get_by_role("dialog")
                expect(
                    dialog.get_by_role("button", name="Reprendre la session")
                ).to_be_disabled()
                dialog.get_by_role("checkbox").check()
                dialog.get_by_role("button", name="Reprendre la session").click()
                expect(field).to_be_enabled()

                field.fill("Brouillon conservé après la coupure")
                time_origin = page.evaluate("performance.timeOrigin")
                page.evaluate("window.__testSockets.at(-1).close()")
                page.wait_for_function(
                    "window.__testSockets.length >= 2 && window.__testSockets.at(-1).readyState === 1"
                )
                expect(page.locator(".connection")).to_contain_text("Connecté")
                expect(page.locator(".session-notice")).to_contain_text(
                    "Session en pause"
                )
                expect(field).to_have_value("Brouillon conservé après la coupure")
                expect(field).to_be_disabled()
                assert page.evaluate("performance.timeOrigin") == time_origin
                page.get_by_title("Reprendre l’assistant").click()
                dialog = page.get_by_role("dialog")
                expect(
                    dialog.get_by_role("button", name="Reprendre la session")
                ).to_be_disabled()
                dialog.get_by_role("checkbox").check()
                dialog.get_by_role("button", name="Reprendre la session").click()
                expect(field).to_be_enabled()
                field.fill("")

                page.get_by_label("Options de la session").click()
                responsive("options")
                page.once("dialog", lambda d: d.accept("Prototype Atlas relu"))
                page.get_by_title("Renommer la session").click()
                expect(page.locator(".brand strong")).to_have_text(
                    "Prototype Atlas relu"
                )
                with page.expect_download() as download:
                    page.get_by_title("Exporter la session").click()
                exported = Path(download.value.path()).read_text(encoding="utf-8")
                assert "Je préparerai le prototype" in exported
                page.get_by_title("Terminer la session").click()
                expect(
                    page.get_by_role("heading", name="Faites une place à Atlas.")
                ).to_be_visible()
                page.get_by_role(
                    "button", name="Prototype Atlas relu", exact=False
                ).click()
                expect(field).to_be_disabled()
                expect(page.locator(".session-notice")).to_contain_text(
                    "Session en pause"
                )
                expect(page.locator(".notes-document")).to_contain_text("prototype")
                # A reload opens the current session paused, never resumes capture.
                page.reload()
                expect(field).to_be_disabled()
                expect(page.locator(".session-notice")).to_contain_text(
                    "Session en pause"
                )
                assert not errors, errors
                report = {
                    "viewports": widths,
                    "views": 7,
                    "meeting_audio_guide": True,
                    "cancel_research": True,
                    "answer_sources": True,
                    "reconnect_paused_without_reload": True,
                    "draft_preserved": True,
                    "tab_audio_capture": audio_report,
                    "consent_pause_resume": True,
                    "source_review": True,
                    "calendar_and_markdown": True,
                    "reopen_paused": True,
                    "page_errors": errors,
                    "providers": "synthetic",
                }
                (ROOT / "tmp/atlas-browser-validation.json").write_text(
                    json.dumps(report, indent=2), encoding="utf-8"
                )
                print(json.dumps(report))
                browser.close()
        finally:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=10)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--serve", action="store_true")
    parser.add_argument("--tab-audio", action="store_true")
    args = parser.parse_args()
    serve() if args.serve else check(tab_audio=args.tab_audio)
