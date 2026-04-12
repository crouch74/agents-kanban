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

export class ApiError extends Error {
  code?: string;
  details?: Record<string, unknown>;
  retryable?: boolean;
  status: number;

  constructor(message: string, status: number, options?: { code?: string; details?: Record<string, unknown>; retryable?: boolean }) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = options?.code;
    this.details = options?.details;
    this.retryable = options?.retryable;
  }
}

async function readError(response: Response): Promise<Error> {
  try {
    const payload = (await response.json()) as {
      detail?: string;
      message?: string;
      error?: {
        code?: string;
        message?: string;
        details?: Record<string, unknown>;
        retryable?: boolean;
      };
    };
    if (payload.error?.message) {
      return new ApiError(payload.error.message, response.status, {
        code: payload.error.code,
        details: payload.error.details,
        retryable: payload.error.retryable,
      });
    }
    if (payload.detail) {
      return new ApiError(payload.detail, response.status);
    }
    if (payload.message) {
      return new ApiError(payload.message, response.status);
    }
  } catch {
    // Ignore JSON parsing issues and fall through.
  }

  return new ApiError(`Request failed: ${response.status}`, response.status);
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
