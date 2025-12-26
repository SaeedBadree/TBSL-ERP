import { useAuthStore } from '~/stores/auth'
import type { PaginatedResponse } from '~/types'

interface FetchOptions {
  method?: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE'
  body?: unknown
  query?: Record<string, string | number | boolean | undefined>
}

export function useApi() {
  const config = useRuntimeConfig()
  const authStore = useAuthStore()

  async function api<T>(path: string, options: FetchOptions = {}): Promise<T> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    }

    if (authStore.token) {
      headers['Authorization'] = `Bearer ${authStore.token}`
    }

    const url = new URL(path, config.public.apiBase)
    if (options.query) {
      Object.entries(options.query).forEach(([key, value]) => {
        if (value !== undefined) {
          url.searchParams.set(key, String(value))
        }
      })
    }

    const response = await fetch(url.toString(), {
      method: options.method ?? 'GET',
      headers,
      body: options.body ? JSON.stringify(options.body) : undefined,
    })

    if (!response.ok) {
      if (response.status === 401) {
        authStore.logout()
      }
      const error = await response.json().catch(() => ({ detail: 'Request failed' }))
      throw new Error(error.detail || 'Request failed')
    }

    if (response.status === 204) {
      return undefined as T
    }

    return response.json()
  }

  return {
    get: <T>(path: string, query?: Record<string, string | number | boolean | undefined>) =>
      api<T>(path, { method: 'GET', query }),

    post: <T>(path: string, body?: unknown) =>
      api<T>(path, { method: 'POST', body }),

    put: <T>(path: string, body?: unknown) =>
      api<T>(path, { method: 'PUT', body }),

    patch: <T>(path: string, body?: unknown) =>
      api<T>(path, { method: 'PATCH', body }),

    delete: <T>(path: string) =>
      api<T>(path, { method: 'DELETE' }),

    upload: async <T>(path: string, file: File, fieldName = 'file'): Promise<T> => {
      const headers: Record<string, string> = {}
      if (authStore.token) {
        headers['Authorization'] = `Bearer ${authStore.token}`
      }

      const formData = new FormData()
      formData.append(fieldName, file)

      const response = await fetch(`${config.public.apiBase}${path}`, {
        method: 'POST',
        headers,
        body: formData,
      })

      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Upload failed' }))
        throw new Error(error.detail || 'Upload failed')
      }

      return response.json()
    },
  }
}

