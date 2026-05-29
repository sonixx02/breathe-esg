let base = import.meta.env.VITE_API_BASE || "";
if (base && !base.endsWith("/api")) {
  // If user provided just the domain, auto-append /api
  base = base.replace(/\/$/, "") + "/api";
} else if (!base) {
  base = "/api";
}
export const API_BASE = base;

export async function apiRequest(path, { token, ...options } = {}) {
  const headers = {
    ...(options.headers || {}),
  };

  // We are keeping the token header in case the user still wants to use the dummy token
  // with backend endpoints that we will set to AllowAny.
  if (token) {
    headers.Authorization = `Token ${token}`;
  }

  let body = options.body;
  if (body && !(body instanceof FormData)) {
    headers["Content-Type"] = "application/json";
    body = JSON.stringify(body);
  }

  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
    body,
  });

  const contentType = response.headers.get("content-type") || "";
  if (!response.ok) {
    let detail = "Request failed.";
    if (contentType.includes("application/json")) {
      const data = await response.json().catch(() => ({}));
      detail = data.detail || detail;
    }
    throw new Error(detail);
  }

  if (!contentType.includes("application/json")) {
    throw new Error("Server returned non-JSON response (possibly HTML or gateway error).");
  }

  const data = await response.json().catch(() => ({}));
  return data;
}
