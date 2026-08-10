const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api";

type RequestOpts = Omit<RequestInit, "body"> & {
  body?: unknown;
  token?: string;
};

async function request<T = unknown>(path: string, opts: RequestOpts = {}): Promise<T> {
  const { body, token, ...init } = opts;
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(init.headers as Record<string, string>),
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });

  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`API ${res.status}: ${text}`);
  }

  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

export const api = {
  get: <T = unknown>(path: string, token?: string) =>
    request<T>(path, { method: "GET", token }),
  post: <T = unknown>(path: string, body?: unknown, token?: string) =>
    request<T>(path, { method: "POST", body, token }),
  put: <T = unknown>(path: string, body?: unknown, token?: string) =>
    request<T>(path, { method: "PUT", body, token }),
  delete: <T = unknown>(path: string, token?: string) =>
    request<T>(path, { method: "DELETE", token }),
};
