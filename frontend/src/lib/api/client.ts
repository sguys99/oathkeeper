const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  constructor(
    public status: number,
    public detail: string,
    public body: Record<string, unknown> = {},
  ) {
    super(detail);
    this.name = "ApiError";
  }
}

let _userEmail: string | null = null;

export function setUserEmail(email: string | null) {
  _userEmail = email;
}

export function getUserEmail(): string | null {
  return _userEmail;
}

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    throw new ApiError(res.status, body.detail ?? "Unknown error", body);
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

function headers(): HeadersInit {
  const h: HeadersInit = { "Content-Type": "application/json" };
  if (_userEmail) h["X-User-Email"] = _userEmail;
  return h;
}

export async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, { headers: headers() });
  return handleResponse<T>(res);
}

export async function post<T>(path: string, body?: unknown): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: headers(),
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });
  return handleResponse<T>(res);
}

export async function put<T>(path: string, body?: unknown): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "PUT",
    headers: headers(),
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });
  return handleResponse<T>(res);
}

export async function del(path: string): Promise<void> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "DELETE",
    headers: headers(),
  });
  await handleResponse<void>(res);
}

export async function upload<T>(path: string, file: File): Promise<T> {
  const formData = new FormData();
  formData.append("file", file);
  const h: HeadersInit = {};
  if (_userEmail) h["X-User-Email"] = _userEmail;
  const res = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: h,
    body: formData,
  });
  return handleResponse<T>(res);
}
