const DEFAULT_API_BASE = "http://127.0.0.1:8000/api/v1";

type ImportMetaWithEnv = ImportMeta & {
  env?: Record<string, string | undefined>;
};

const env = (import.meta as ImportMetaWithEnv).env ?? {};
const configuredApiBase = env.VITE_API_BASE?.trim();

export const API_BASE = configuredApiBase && configuredApiBase.length > 0 ? configuredApiBase : DEFAULT_API_BASE;

export const WS_BASE =
  env.VITE_WS_BASE?.trim() ||
  API_BASE.replace(/^http:\/\//u, "ws://").replace(/^https:\/\//u, "wss://") +
    "/ws";

async function readError(response: Response): Promise<Error> {
  try {
    const payload = (await response.json()) as { detail?: string; message?: string };
    if (payload.detail) {
      return new Error(payload.detail);
    }
    if (payload.message) {
      return new Error(payload.message);
    }
  } catch {
    // Ignore JSON parsing issues and fall through.
  }

  return new Error(`Request failed: ${response.status}`);
}

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
    ...init,
  });

  if (!response.ok) {
    throw await readError(response);
  }

  return (await response.json()) as T;
}

export function fetchJson<T>(path: string): Promise<T> {
  return requestJson<T>(path);
}

export function postJson<T>(path: string, body: unknown): Promise<T> {
  return requestJson<T>(path, {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function patchJson<T>(path: string, body: unknown): Promise<T> {
  return requestJson<T>(path, {
    method: "PATCH",
    body: JSON.stringify(body),
  });
}
