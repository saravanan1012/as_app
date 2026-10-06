export default defineNuxtRouteMiddleware(async () => {
  const auth = useAuthStore()
  if (!auth.ready) await auth.fetchMe()
  if (!auth.isLoggedIn) {
    return navigateTo('/login')
  }
})
