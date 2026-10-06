export default defineNuxtRouteMiddleware(async () => {
  const auth = useAuthStore()
  if (!auth.ready) await auth.fetchMe()
  if (!auth.isLoggedIn) return navigateTo('/login')

  if (!auth.hasPermission('b2b.portal')) {
    if (auth.hasPermission('dashboard.read')) return navigateTo('/admin')
    if (auth.user?.role === 'CUSTOMER') return navigateTo('/store/orders')
    return navigateTo('/login')
  }
})
