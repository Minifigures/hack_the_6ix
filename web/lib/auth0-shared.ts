// Shared between server and client code; no server-only imports here.
export const STEP_UP_ACR =
  "http://schemas.openid.net/pape/policies/2007/06/multi-factor";

export const ENTERED_KEY = "innsight-entered";
export const MFA_KEY = "innsight-mfa-verified";

const GOOGLE_CONNECTION = "google-oauth2";

/** Auth0 login that skips the Universal Login picker and goes straight to Google. */
export function loginHref(returnTo = "/"): string {
  const params = new URLSearchParams({
    connection: GOOGLE_CONNECTION,
    returnTo,
  });
  return `/auth/login?${params.toString()}`;
}

/** Clears local “entered app” + MFA markers so logout lands on the marketing page. */
export function clearLocalAuthState(): void {
  try {
    sessionStorage.removeItem(ENTERED_KEY);
    localStorage.removeItem(MFA_KEY);
  } catch {
    // ignore (SSR / private mode)
  }
}

/** Always return to the landing page after Auth0 logout (absolute URL required). */
export function logoutHref(): string {
  // No trailing slash — must match Auth0 Allowed Logout URLs exactly.
  const returnTo =
    typeof window !== "undefined"
      ? window.location.origin
      : "http://localhost:3000";
  const params = new URLSearchParams({ returnTo });
  return `/auth/logout?${params.toString()}`;
}
