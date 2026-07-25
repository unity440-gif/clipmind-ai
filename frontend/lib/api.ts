/**
 * Small helper for calling the ClipMind AI backend.
 * Centralizes the base URL and error handling so pages don't repeat it.
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL;

export async function apiFetch(path: string, options: RequestInit = {}) {
  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
  });

  if (!response.ok) {
    const errorBody = await response.json().catch(() => null);
    const message = errorBody?.detail || "Something went wrong. Please try again.";
    throw new Error(message);
  }

  return response.json();
}