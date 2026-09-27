import { act, renderHook } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { useAtlas } from "./useAtlas";

const mocks = vi.hoisted(() => ({
  bootstrap: vi.fn(),
  capture: vi.fn(),
  stopCapture: vi.fn(),
  stopPlayback: vi.fn(),
}));

class FakeSocket {
  static instances: FakeSocket[] = [];
  readyState = 0;
  onopen?: () => Promise<void>;
  onclose?: (event: { code: number }) => void;
  onmessage?: (event: { data: string }) => void;
  sent: Array<Record<string, unknown>> = [];
  constructor() {
    FakeSocket.instances.push(this);
  }
  send(text: string) {
    this.sent.push(JSON.parse(text));
  }
  async open() {
    this.readyState = 1;
    await this.onopen?.();
  }
  close(code = 1000) {
    this.readyState = 3;
    this.onclose?.({ code });
  }
  receive(message: object) {
    this.onmessage?.({ data: JSON.stringify(message) });
  }
}

vi.mock("../api", () => ({
  bootstrap: mocks.bootstrap,
  liveSocket: () => new FakeSocket(),
  send: (socket: FakeSocket, message: object) => {
    if (socket.readyState === 1) socket.send(JSON.stringify(message));
  },
  deleteAtlasSession: vi.fn(),
  exportAtlasSession: vi.fn(),
  renameAtlasSession: vi.fn(),
}));
vi.mock("../audio", () => ({
  AudioBridge: class {
    start = mocks.capture;
    stopCapture = mocks.stopCapture;
    stopPlayback = mocks.stopPlayback;
    stopCue = vi.fn();
  },
}));

const pausedState = {
  session_id: "session-one",
  session_status: "paused",
  language: "fr",
  capture_mode: "microphone",
};
const payload = {
  protocol_version: 12,
  display_name: "Atlas",
  access_token: "token-one",
  state: pausedState,
  sessions: [],
};

beforeEach(() => {
  vi.useFakeTimers();
  vi.clearAllMocks();
  FakeSocket.instances = [];
  mocks.bootstrap.mockResolvedValue(payload);
  mocks.stopCapture.mockResolvedValue(undefined);
});
afterEach(() => {
  vi.useRealTimers();
});

describe("connection recovery", () => {
  it("refreshes authentication and preserves the draft without resuming capture", async () => {
    const { result, unmount } = renderHook(() => useAtlas());
    const first = FakeSocket.instances[0];
    await act(async () => {
      await first.open();
      first.receive({ type: "backend.hello", protocol_version: 12 });
    });
    act(() => result.current.setManual("Brouillon à conserver"));
    act(() => first.close(1006));
    expect(mocks.stopCapture).toHaveBeenCalled();
    expect(mocks.stopPlayback).toHaveBeenCalled();
    expect(result.current.consent).toBe(false);
    expect(result.current.reconnecting).toBe(true);
    mocks.bootstrap.mockResolvedValue({
      ...payload,
      access_token: "token-two",
    });
    await act(async () => {
      await vi.advanceTimersByTimeAsync(500);
    });
    const second = FakeSocket.instances[1];
    await act(async () => {
      await second.open();
      second.receive({ type: "backend.hello", protocol_version: 12 });
      second.receive({
        type: "state.snapshot",
        state: pausedState,
        sessions: [],
      });
    });
    expect(second.sent[0].access_token).toBe("token-two");
    expect(second.sent[0].client_id).toBe(first.sent[0].client_id);
    expect(result.current.manual).toBe("Brouillon à conserver");
    expect(result.current.state?.session_status).toBe("paused");
    expect(result.current.connected).toBe(true);
    expect(result.current.reconnecting).toBe(false);
    expect(mocks.capture).not.toHaveBeenCalled();
    expect(second.sent.some((m) => m.command === "resume")).toBe(false);
    unmount();
  });

  it("backs off across failed connections and cancels retries on unmount", async () => {
    const { unmount } = renderHook(() => useAtlas());
    await act(async () => {
      FakeSocket.instances[0].close(1006);
    });
    await act(async () => {
      await vi.advanceTimersByTimeAsync(500);
    });
    expect(FakeSocket.instances).toHaveLength(2);
    act(() => FakeSocket.instances[1].close(1006));
    await act(async () => {
      await vi.advanceTimersByTimeAsync(999);
    });
    expect(FakeSocket.instances).toHaveLength(2);
    await act(async () => {
      await vi.advanceTimersByTimeAsync(1);
    });
    expect(FakeSocket.instances).toHaveLength(3);
    act(() => FakeSocket.instances[2].close(1006));
    unmount();
    await vi.advanceTimersByTimeAsync(20000);
    expect(FakeSocket.instances).toHaveLength(3);
  });

  it("does not retry rejected connections until the user asks", async () => {
    const { result, unmount } = renderHook(() => useAtlas());
    await act(async () => {
      FakeSocket.instances[0].close(1008);
    });
    await act(async () => {
      await vi.advanceTimersByTimeAsync(20000);
    });
    expect(FakeSocket.instances).toHaveLength(1);
    expect(result.current.reconnecting).toBe(false);
    act(() => result.current.reconnect());
    expect(FakeSocket.instances).toHaveLength(2);
    unmount();
  });
});
