const TOKEN_KEY = "mer_token";

export class ApiError extends Error {
  code: string;
  details?: Record<string, unknown>;

  constructor(message: string, code: string, details?: Record<string, unknown>) {
    super(message);
    this.code = code;
    this.details = details;
  }
}

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken(): void {
  localStorage.removeItem(TOKEN_KEY);
}

export async function api<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  if (!headers.has("Content-Type") && init.body) headers.set("Content-Type", "application/json");
  const token = getToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);
  const res = await fetch(path, { ...init, headers });
  if (res.headers.get("content-type")?.includes("text/html")) {
    if (!res.ok) throw new ApiError(res.statusText, "HTTP");
    return (await res.text()) as T;
  }
  const data = (await res.json().catch(() => ({}))) as {
    message?: string;
    code?: string;
    details?: Record<string, unknown>;
  };
  if (!res.ok) {
    throw new ApiError(data.message || res.statusText, data.code || "HTTP", data.details);
  }
  return data as T;
}

export async function login(username: string, password: string): Promise<void> {
  const data = await api<{ access_token: string }>("/api/v1/auth/login", {
    method: "POST",
    body: JSON.stringify({ username, password }),
  });
  setToken(data.access_token);
}

export function messageOf(e: unknown): string {
  return e instanceof Error ? e.message : String(e);
}
