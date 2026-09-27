import { fireEvent, render, screen } from "@testing-library/react";
import { Circle } from "lucide-react";
import { describe, expect, it, vi } from "vitest";

import { WorkspaceNavigation } from "./WorkspaceNavigation";

describe("WorkspaceNavigation", () => {
  it("keeps the view stable on hover and selects on click", () => {
    const select = vi.fn();
    render(
      <WorkspaceNavigation
        active="flow"
        items={[
          { view: "flow", label: "Flow", icon: Circle },
          { view: "notes", label: "Notes", icon: Circle },
        ]}
        onSelect={select}
      />,
    );
    const notes = screen.getByTitle("Notes");
    fireEvent.mouseEnter(notes);
    fireEvent.focus(notes);
    fireEvent.mouseLeave(notes);
    expect(select).not.toHaveBeenCalled();
    expect(screen.getByTitle("Flow").getAttribute("aria-pressed")).toBe("true");
    expect(notes.getAttribute("aria-pressed")).toBe("false");
    fireEvent.click(notes);
    expect(select).toHaveBeenCalledWith("notes");
  });
});
