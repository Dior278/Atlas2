import {
  Columns3,
  CheckCheck,
  ArrowLeft,
  FileText,
  MessageSquareText,
  Send,
  Workflow,
} from "lucide-react";
import { send } from "./api";
import { SessionHome, Consent, LANGUAGES } from "./components/SessionHome";
import { MinutesView } from "./components/MinutesView";
import { AtlasSubtitles } from "./components/AtlasSubtitles";
import { NotesView } from "./components/NotesView";
import { SessionControls } from "./components/SessionControls";
import {
  WorkspaceNavigation,
  type WorkspaceView,
} from "./components/WorkspaceNavigation";
import { WorkflowCanvas } from "./components/WorkflowCanvas";
import { Board, Transcript, ActivityStrip } from "./components/WorkspaceViews";
import { useAtlas } from "./hooks/useAtlas";
export function App() {
  const {
    state,
    sessions,
    partial,
    connected,
    reconnecting,
    reconnect,
    view,
    setView,
    displayName,
    captureMode,
    setCaptureMode,
    language,
    manual,
    setManual,
    error,
    setError,
    audioStatus,
    audioLevel,
    subtitlesEnabled,
    promptBarVisible,
    subtitle,
    consent,
    setConsent,
    resumePrompt,
    setResumePrompt,
    starting,
    socketRef,
    start,
    command,
    resumeSession,
    changeLanguage,
    renameSession,
    deleteSession,
    exportSession,
    inject,
    toggleSubtitles,
    togglePromptBar,
  } = useAtlas();
  if (!state)
    return (
      <main className="loading">{error || `Connexion à ${displayName}…`}</main>
    );
  const listening = state.session_status === "listening";
  const capturing = audioStatus === "active" || audioStatus === "requesting";
  const navigation: Array<{
    view: WorkspaceView;
    label: string;
    icon: typeof Workflow;
  }> = [
    { view: "notes", label: "Notes", icon: FileText },
    { view: "board", label: "Tableau", icon: Columns3 },
    { view: "minutes", label: "Engagements", icon: CheckCheck },
    { view: "transcript", label: "Conversation", icon: MessageSquareText },
    { view: "flow", label: "Agents", icon: Workflow },
  ];

  const inSession =
    state.session_status !== "idle" && state.session_status !== "closed";
  return (
    <main>
      <header className={listening ? "session-header live" : "session-header"}>
        <div className="brand">
          {inSession && (
            <button
              className="icon-button back-button"
              title="Terminer et revenir à l’accueil"
              onClick={() => void command("stop")}
            >
              <ArrowLeft size={18} />
            </button>
          )}
          <img src="/atlas-mark.svg" alt="" />
          <div>
            <strong>{inSession ? state.title : displayName}</strong>
            <small>
              {inSession
                ? `Atlas · ${listening ? "En cours" : "En pause"}`
                : "Votre coéquipier de réunion"}
            </small>
          </div>
        </div>
        {inSession && (
          <WorkspaceNavigation
            active={view}
            items={navigation}
            onSelect={setView}
          />
        )}
        <div className="header-actions">
          {state.session_status !== "idle" &&
            state.session_status !== "closed" && (
              <>
                <SessionControls
                  language={language}
                  languages={LANGUAGES}
                  canCurate={
                    state.cards.length > 0 ||
                    (state.notes_document?.topics?.length ?? 0) > 0
                  }
                  curatorRunning={state.agent_runs.some(
                    (run) =>
                      run.agent === "coordinator" && run.status === "running",
                  )}
                  voiceMode={state.voice_mode}
                  subtitlesEnabled={subtitlesEnabled}
                  promptBarVisible={promptBarVisible}
                  listening={listening}
                  onLanguage={changeLanguage}
                  onCurate={() =>
                    socketRef.current &&
                    send(socketRef.current, { type: "board.curate" })
                  }
                  onToggleVoice={() =>
                    socketRef.current &&
                    send(socketRef.current, {
                      type: "voice.mode",
                      mode: state.voice_mode === "muted" ? "active" : "muted",
                    })
                  }
                  onToggleSubtitles={toggleSubtitles}
                  onTogglePromptBar={togglePromptBar}
                  onRename={() =>
                    state.session_id &&
                    void renameSession(state.session_id, state.title)
                  }
                  onExport={() =>
                    state.session_id && void exportSession(state.session_id)
                  }
                  onPauseResume={() =>
                    void command(listening && capturing ? "pause" : "resume")
                  }
                  onEnd={() => void command("stop")}
                />
              </>
            )}
          <div className={`connection ${connected ? "online" : ""}`}>
            <i />
            {connected
              ? "Connecté"
              : reconnecting
                ? "Reconnexion…"
                : "Hors ligne"}
          </div>
        </div>
      </header>

      {state.session_status === "idle" || state.session_status === "closed" ? (
        <SessionHome
          sessions={sessions}
          language={language}
          captureMode={captureMode}
          consent={consent}
          connected={connected}
          starting={starting}
          error={error}
          onConsent={setConsent}
          onLanguage={changeLanguage}
          onCapture={setCaptureMode}
          onStart={() => void start()}
          onOpen={(id) => void resumeSession(id)}
          onRename={(id, title) => void renameSession(id, title)}
          onDelete={(id, title) => void deleteSession(id, title)}
          onExport={(id) => void exportSession(id)}
        />
      ) : (
        <>
          {!connected && (
            <div className="session-notice" role="status">
              {reconnecting
                ? "Reconnexion en cours. L’écoute reste arrêtée jusqu’à votre reprise."
                : "Connexion interrompue. L’écoute est arrêtée."}{" "}
              <button onClick={reconnect}>Réessayer maintenant</button>
            </div>
          )}
          {!listening && connected && (
            <div className="session-notice">
              Session en pause · Vous pouvez relire et exporter votre travail.{" "}
              <button
                onClick={() => {
                  setConsent(false);
                  setResumePrompt(true);
                }}
              >
                Reprendre
              </button>
            </div>
          )}
          {resumePrompt && (
            <div className="dialog-backdrop">
              <section
                className="resume-dialog"
                role="dialog"
                aria-modal="true"
                aria-labelledby="resume-title"
              >
                <h2 id="resume-title">Reprendre avec Atlas</h2>
                <p>
                  La source reste celle de cette session. L’analyse reprend
                  après votre confirmation.
                </p>
                <Consent checked={consent} onChange={setConsent} />
                <div>
                  <button onClick={() => setResumePrompt(false)}>
                    Annuler
                  </button>
                  <button
                    className="start"
                    disabled={!consent || !connected}
                    onClick={() => void command("resume")}
                  >
                    Reprendre la session
                  </button>
                </div>
              </section>
            </div>
          )}
          <section className="view-stage">
            {view === "flow" && (
              <WorkflowCanvas
                state={state}
                audioStatus={audioStatus}
                onCancelTask={
                  connected
                    ? (taskId) =>
                        socketRef.current &&
                        send(socketRef.current, {
                          type: "task.cancel",
                          task_id: taskId,
                        })
                    : undefined
                }
              />
            )}
            {view === "board" && <Board state={state} />}
            {view === "notes" && <NotesView state={state} />}
            {view === "minutes" && <MinutesView state={state} />}
            {view === "transcript" && (
              <Transcript state={state} partial={partial} />
            )}
          </section>
          {(promptBarVisible || captureMode === "text") && (
            <section className="manual command-bar">
              <input
                aria-label="Message à Atlas"
                disabled={!listening || !connected}
                maxLength={12000}
                value={manual}
                onChange={(event) => setManual(event.target.value)}
                onKeyDown={(event) => event.key === "Enter" && inject()}
                placeholder={
                  listening
                    ? "Une idée, une question… Adressez-vous à Atlas."
                    : "Reprenez la session pour écrire à Atlas"
                }
              />
              <button
                disabled={!listening || !connected || !manual.trim()}
                onClick={inject}
                title="Envoyer"
                aria-label="Envoyer"
              >
                <Send size={17} />
              </button>
            </section>
          )}
          {error && (
            <div className="error global-error" role="alert">
              {error}
              <button aria-label="Fermer l’erreur" onClick={() => setError("")}>
                ×
              </button>
            </div>
          )}
          <ActivityStrip
            state={state}
            partial={partial}
            audioStatus={audioStatus}
            audioLevel={audioLevel}
          />
          <AtlasSubtitles
            enabled={subtitlesEnabled}
            text={subtitle}
            companionName={state.identity_name}
          />
        </>
      )}
    </main>
  );
}
