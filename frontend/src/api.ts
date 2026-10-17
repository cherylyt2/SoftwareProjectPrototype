/** Small typed client for the same-origin Flask API. */

export class ApiError extends Error {
  status: number

  constructor(message: string, status: number) {
    super(message)
    this.status = status
  }
}

export async function apiRequest<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers)
  if (options.body && !(options.body instanceof FormData) && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json')
  }
  const response = await fetch(path, {
    ...options,
    credentials: 'include',
    headers,
  })
  const data = await response.json().catch(() => ({}))
  if (!response.ok) throw new ApiError(data.error ?? 'The request could not be completed.', response.status)
  return data as T
}