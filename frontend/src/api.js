// Backend address. Empty by default so `npm run dev` goes through the Vite proxy (/api -> :8000).
// Set VITE_API_BASE (e.g. https://cf-trainer-api.onrender.com) when the API lives elsewhere.
const API_BASE = (import.meta.env.VITE_API_BASE ?? "").replace(/\/+$/, "");

export class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

function errorMessage(status, body) {
  if (typeof body?.detail === "string") return body.detail;
  if (status === 422) return "That does not look like a valid Codeforces handle.";
  return `The server answered with HTTP ${status}.`;
}

async function request(path, options) {
  let response;
  try {
    response = await fetch(`${API_BASE}${path}`, options);
  } catch {
    throw new ApiError("Cannot reach the CF Trainer server. Check your connection and try again.", 0);
  }
  let body = null;
  try {
    body = await response.json();
  } catch {
    // Not JSON (e.g. a proxy error page); fall back to the status code below.
  }
  if (!response.ok) throw new ApiError(errorMessage(response.status, body), response.status);
  return body;
}

const userPath = (handle) => `/api/users/${encodeURIComponent(handle)}`;

/** Fetch the user's latest data from Codeforces and store it on the server. */
export function syncUser(handle) {
  return request(`${userPath(handle)}/sync`, { method: "POST" });
}

/** The analysis report built from the stored data. */
export function getReport(handle) {
  return request(`${userPath(handle)}/report`);
}
