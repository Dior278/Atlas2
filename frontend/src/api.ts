import type { Bootstrap, ClientMessage } from "./protocol";

let accessToken = "";

export async function bootstrap(): Promise<Bootstrap> {
  const response = await fetch("/v1/bootstrap");
  if (!response.ok) throw new Error(`Bootstrap failed: ${response.status}`);
  const payload = (await response.json()) as Bootstrap;
  accessToken = payload.access_token;
  return payload;
}

export async function request(
  path: string,
  method = "GET",
  body?: object,
): Promise<Response> {
  const response = await fetch(path, {
    method,
    headers: {
      Authorization: `Bearer ${accessToken}`,
      "Content-Type": "application/json",
    },
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(
      typeof error.detail === "string"
        ? error.detail
        : `Opération indisponible (${response.status}).`,
    );
  }
  return response;
}

export async function download(path: string, filename: string): Promise<void> {
  const response = await request(path);
  const url = URL.createObjectURL(await response.blob());
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

export function liveSocket(): WebSocket {
  const scheme = location.protocol === "https:" ? "wss" : "ws";
  return new WebSocket(`${scheme}://${location.host}/v1/live`);
}

export function send(socket: WebSocket, message: ClientMessage): void {
  if (socket.readyState === WebSocket.OPEN)
    socket.send(JSON.stringify(message));
}

export async function renameAtlasSession(
  sessionId: string,
  title: string,
): Promise<void> {
  await request(`/v1/sessions/${encodeURIComponent(sessionId)}`, "PATCH", {
    title,
  });
}

export async function deleteAtlasSession(sessionId: string): Promise<void> {
  await request(`/v1/sessions/${encodeURIComponent(sessionId)}`, "DELETE");
}

export function exportAtlasSession(sessionId: string): Promise<void> {
  return download(
    `/v1/sessions/${encodeURIComponent(sessionId)}/export`,
    `${sessionId}.md`,
  );
}
