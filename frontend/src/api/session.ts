/**
 * The session id: created when the page loads, kept in memory only, sent as `X-Session-Id` on
 * every call. Reloading the page starts a new session.
 */
export const sessionId: string = crypto.randomUUID();
