/**
 * API Client for Backend Integration
 * 
 * Provides a centralized API client for making requests to the backend.
 * Supports both REST and future tRPC integration.
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export interface ApiError {
  message: string
  code?: string
  status?: number
}

export class ApiClientError extends Error {
  code?: string
  status?: number

  constructor(message: string, code?: string, status?: number) {
    super(message)
    this.name = 'ApiClientError'
    this.code = code
    this.status = status
  }
}

/**
 * Get authentication token from storage
 */
function getAuthToken(): string | null {
  if (typeof window === 'undefined') return null
  return localStorage.getItem('auth_token') || sessionStorage.getItem('auth_token')
}

/**
 * Get API headers with authentication
 */
function getHeaders(customHeaders?: Record<string, string>): HeadersInit {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...customHeaders,
  }

  const token = getAuthToken()
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }

  return headers
}

/**
 * Handle API response
 */
async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let errorMessage = `HTTP ${response.status}: ${response.statusText}`
    let errorCode: string | undefined

    try {
      const errorData = await response.json()
      errorMessage = errorData.message || errorData.detail || errorMessage
      errorCode = errorData.code
    } catch {
      // If response is not JSON, use status text
    }

    throw new ApiClientError(errorMessage, errorCode, response.status)
  }

  // Handle empty responses
  const contentType = response.headers.get('content-type')
  if (!contentType || !contentType.includes('application/json')) {
    return {} as T
  }

  return response.json()
}

/**
 * API Client class
 */
export class ApiClient {
  private baseUrl: string

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl.replace(/\/$/, '')
  }

  /**
   * GET request
   */
  async get<T>(endpoint: string, options?: RequestInit): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`
    const response = await fetch(url, {
      method: 'GET',
      headers: getHeaders(options?.headers as Record<string, string>),
      ...options,
    })

    return handleResponse<T>(response)
  }

  /**
   * POST request
   */
  async post<T>(endpoint: string, data?: unknown, options?: RequestInit): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`
    const response = await fetch(url, {
      method: 'POST',
      headers: getHeaders(options?.headers as Record<string, string>),
      body: data ? JSON.stringify(data) : undefined,
      ...options,
    })

    return handleResponse<T>(response)
  }

  /**
   * PUT request
   */
  async put<T>(endpoint: string, data?: unknown, options?: RequestInit): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`
    const response = await fetch(url, {
      method: 'PUT',
      headers: getHeaders(options?.headers as Record<string, string>),
      body: data ? JSON.stringify(data) : undefined,
      ...options,
    })

    return handleResponse<T>(response)
  }

  /**
   * PATCH request
   */
  async patch<T>(endpoint: string, data?: unknown, options?: RequestInit): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`
    const response = await fetch(url, {
      method: 'PATCH',
      headers: getHeaders(options?.headers as Record<string, string>),
      body: data ? JSON.stringify(data) : undefined,
      ...options,
    })

    return handleResponse<T>(response)
  }

  /**
   * DELETE request
   */
  async delete<T>(endpoint: string, options?: RequestInit): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`
    const response = await fetch(url, {
      method: 'DELETE',
      headers: getHeaders(options?.headers as Record<string, string>),
      ...options,
    })

    return handleResponse<T>(response)
  }
}

// Default API client instance
export const apiClient = new ApiClient()

// Convenience functions
export const api = {
  get: <T>(endpoint: string, options?: RequestInit) => apiClient.get<T>(endpoint, options),
  post: <T>(endpoint: string, data?: unknown, options?: RequestInit) => apiClient.post<T>(endpoint, data, options),
  put: <T>(endpoint: string, data?: unknown, options?: RequestInit) => apiClient.put<T>(endpoint, data, options),
  patch: <T>(endpoint: string, data?: unknown, options?: RequestInit) => apiClient.patch<T>(endpoint, data, options),
  delete: <T>(endpoint: string, options?: RequestInit) => apiClient.delete<T>(endpoint, options),
}

