import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { SessionControls } from "./SessionControls";

function renderControls(
  overrides: Partial<Parameters<typeof SessionControls>[0]> = {},
) {
  const actions = {
    onLanguage: vi.fn(),
    onCurate: vi.fn(),
    onToggleVoice: vi.fn(),
    onToggleSubtitles: vi.fn(),
    onTogglePromptBar: vi.fn(),
    onRename: vi.fn(),
    onExport: vi.fn(),
    onPauseResume: vi.fn(),
    onEnd: vi.fn(),
  };
  render(
    <SessionControls
      language="en"
      languages={[
        { value: "en", label: "English" },
        { value: "fr", label: "Français" },
      ]}
      canCurate
      curatorRunning={false}
      voiceMode="active"
      subtitlesEnabled
      promptBarVisible
      listening
      {...actions}
      {...overrides}
    />,
  );
  return actions;
}

describe("SessionControls", () => {
  it("connects every visible action", () => {
    const actions = renderControls();
    fireEvent.click(screen.getByTitle("Organiser le tableau"));
    fireEvent.click(screen.getByTitle("Couper la voix"));
    fireEvent.click(screen.getByTitle("Masquer les sous-titres"));
    fireEvent.click(screen.getByTitle("Masquer la saisie"));
    fireEvent.click(screen.getByTitle("Renommer la session"));
    fireEvent.click(screen.getByTitle("Exporter la session"));
    fireEvent.click(screen.getByTitle("Mettre en pause"));
    fireEvent.click(screen.getByTitle("Terminer la session"));
    expect(actions.onCurate).toHaveBeenCalledOnce();
    expect(actions.onToggleVoice).toHaveBeenCalledOnce();
    expect(actions.onToggleSubtitles).toHaveBeenCalledOnce();
    expect(actions.onTogglePromptBar).toHaveBeenCalledOnce();
    expect(actions.onRename).toHaveBeenCalledOnce();
    expect(actions.onExport).toHaveBeenCalledOnce();
    expect(actions.onPauseResume).toHaveBeenCalledOnce();
    expect(actions.onEnd).toHaveBeenCalledOnce();
  });

  it("disables curation when there is no board content", () => {
    const actions = renderControls({ canCurate: false });
    const button = screen.getByTitle(
      "Aucune idée à organiser",
    ) as HTMLButtonElement;
    expect(button.disabled).toBe(true);
    fireEvent.click(button);
    expect(actions.onCurate).not.toHaveBeenCalled();
  });

  it("reports voice and subtitle state accessibly", () => {
    renderControls({
      voiceMode: "muted",
      subtitlesEnabled: false,
      promptBarVisible: false,
    });
    expect(
      screen.getByTitle("Activer la voix").getAttribute("aria-pressed"),
    ).toBe("false");
    expect(
      screen
        .getByTitle("Afficher les sous-titres")
        .getAttribute("aria-pressed"),
    ).toBe("false");
    expect(
      screen.getByTitle("Afficher la saisie").getAttribute("aria-pressed"),
    ).toBe("false");
  });
});
