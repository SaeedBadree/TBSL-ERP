import { defineStore } from 'pinia'
import type { User, TokenResponse } from '~/types'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: null as string | null,
    user: null as User | null,
  }),

  getters: {
    isAuthenticated: (state) => !!state.token,
    role: (state) => state.user?.role ?? null,
  },

  actions: {
    setAuth(data: TokenResponse) {
      this.token = data.access_token
      if (import.meta.client) {
        localStorage.setItem('token', data.access_token)
      }
    },

    setUser(user: User) {
      this.user = user
    },

    logout() {
      this.token = null
      this.user = null
      if (import.meta.client) {
        localStorage.removeItem('token')
      }
      navigateTo('/login')
    },

    init() {
      if (import.meta.client) {
        const stored = localStorage.getItem('token')
        if (stored) {
          this.token = stored
        }
      }
    },
  },
})

