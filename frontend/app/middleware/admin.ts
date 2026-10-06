export default defineNuxtRouteMiddleware(async () => {
  const auth = useAuthStore()
  const adminCtx = useAdminContextStore()
  if (!auth.ready) await auth.fetchMe()
  if (!auth.isLoggedIn) return navigateTo('/login')

  adminCtx.hydrate()

  const staff = auth.hasPermission('dashboard.read')
    || auth.hasPermission('sales.orders.read')
    || auth.hasPermission('purchase.orders.read')
    || auth.hasPermission('catalog.items.read')

  if (!staff && !auth.hasPermission('platform.vendors.manage')) {
    return navigateTo('/')
  }

  if (auth.user?.role === 'SUPER_ADMIN' && !adminCtx.vendorId) {
    // Super admin must pick a vendor first (except when coming from platform deep-link)
    return navigateTo('/platform')
  }

  if (auth.user?.role === 'CUSTOMER') {
    return navigateTo('/store/orders')
  }

  if (['DISTRIBUTOR', 'DEALER', 'RETAILER'].includes(auth.user?.role || '')) {
    return navigateTo('/b2b')
  }
})
