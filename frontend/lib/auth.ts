/**
 * Auth helpers for the frontend.
 * Reads the JWT from localStorage and fetches the current user from the backend.
 */

import { apiFetch } from "./api";

export interface CurrentUser {
  id: string;
  email: string;
  full_name: string | null;
  credits_remaining: number;
}

export function getToken(): string | null {
  if (typeof window === "undefined") return null; // guards against server-side rendering
  return localStorage.getItem("access_token");
}

export async function getCurrentUser(): Promise<CurrentUser> {
  const token = getToken();
  if (!token) throw new Error("Not logged in");

  return apiFetch("/auth/me", {
    headers: { Authorization: `Bearer ${token}` },
  });
}

export function logout() {
  localStorage.removeItem("access_token");
  window.location.href = "/login";
}