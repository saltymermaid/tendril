/**
 * Global fetch wrapper that intercepts 401 (Unauthorized) responses and
 * redirects the user to /login. This eliminates confusing "Failed to load …"
 * errors that appear when a session has simply expired.
 *
 * Auth-internal routes (auth/status, auth/login, auth/logout, auth/refresh)
 * should continue to use raw fetch() so they can handle auth flow themselves.
 */
export async function apiFetch(input: string, init?: RequestInit): Promise<Response> {
  const res = await fetch(input, { credentials: 'include', ...init })
  if (res.status === 401) {
    window.location.href = '/login'
    // Return a never-resolving promise so the calling code doesn't proceed
    return new Promise(() => {})
  }
  return res
}
