export class ApiError extends Error {
  code: string;
  status: number;
  details: Record<string, unknown>;

  constructor(message: string, code: string, status: number, details: Record<string, unknown>) {
    super(message);
    this.code = code;
    this.status = status;
    this.details = details;
  }
}

const base = import.meta.env.VITE_API_BASE ?? "";

export function token(): string {
  return localStorage.getItem("mer_token") ?? "";
}

export function setSession(accessToken: string, username: string): void {
  localStorage.setItem("mer_token", accessToken);
  localStorage.setItem("mer_user", username);
}

export function clearSession(): void {
  localStorage.removeItem("mer_token");
  localStorage.removeItem("mer_user");
}

export function currentUser(): string {
  return localStorage.getItem("mer_user") ?? "";
}

export async function api<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  if (!headers.has("Content-Type") && init.body) {
    headers.set("Content-Type", "application/json");
  }
  const access = token();
  if (access) {
    headers.set("Authorization", `Bearer ${access}`);
  }
  const response = await fetch(`${base}${path}`, { ...init, headers });
  if (response.status === 204) {
    return undefined as T;
  }
  const text = await response.text();
  const data = text ? (JSON.parse(text) as Record<string, unknown>) : {};
  if (!response.ok) {
    throw new ApiError(
      String(data.message ?? response.statusText),
      String(data.code ?? "INTERNAL_ERROR"),
      response.status,
      (data.details as Record<string, unknown>) ?? {},
    );
  }
  return data as T;
}
