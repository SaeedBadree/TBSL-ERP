import { useAuthStore } from '~/stores/auth'

export default defineNuxtRouteMiddleware((to) => {
  const authStore = useAuthStore()

  // Initialize from localStorage on client
  if (import.meta.client && !authStore.token) {
    authStore.init()
  }

  // Allow login page without auth
  if (to.path === '/login') {
    return
  }

  // Redirect to login if not authenticated
  if (!authStore.token) {
    return navigateTo('/login')
  }
})

