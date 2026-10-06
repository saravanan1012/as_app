import { defineStore } from 'pinia'

export type AuthUser = {
  id: number
  email: string
  name: string
  role: string
  vendor_id: number | null
  permissions: string[]
  default_redirect: string
}

export const useAuthStore = defineStore('auth', () => {
  const user = ref<AuthUser | null>(null)
  const ready = ref(false)

  const isLoggedIn = computed(() => !!user.value)
  const permissions = computed(() => new Set(user.value?.permissions || []))

  function hasPermission(code: string) {
    const have = permissions.value
    if (have.has(code)) return true
    const idx = code.lastIndexOf('.')
    if (idx < 0) return false
    const resource = code.slice(0, idx)
    const action = code.slice(idx + 1)
    if (action === 'read') {
      return have.has(`${resource}.write`) || have.has(`${resource}.manage`)
    }
    if (action === 'write') return have.has(`${resource}.manage`)
    return false
  }

  async function fetchMe() {
    const { api } = useApi()
    try {
      const res = await api<AuthUser>('/auth/me')
      user.value = res.data
    } catch {
      user.value = null
    } finally {
      ready.value = true
    }
  }

  async function login(email: string, password: string) {
    const { api } = useApi()
    const res = await api<AuthUser>('/auth/login', {
      method: 'POST',
      body: { email, password }
    })
    user.value = res.data
    return res.data
  }

  async function logout() {
    const { api } = useApi()
    try {
      await api('/auth/logout', { method: 'POST' })
    } finally {
      user.value = null
    }
  }

  async function registerStore(email: string, password: string, name: string) {
    const { api } = useApi()
    const res = await api<AuthUser>('/store/auth/register', {
      method: 'POST',
      body: { email, password, name }
    })
    // register sets cookie; refresh profile
    await fetchMe()
    return res.data
  }

  return {
    user,
    ready,
    isLoggedIn,
    permissions,
    hasPermission,
    fetchMe,
    login,
    logout,
    registerStore
  }
})
