/** Login redirect helper — mirrors backend default_redirect / RBAC matrix. */
export function useRedirect() {
  const auth = useAuthStore()
  const vendor = useVendorStore()

  function resolveHome(user = auth.user) {
    if (!user) return '/'
    if (user.default_redirect) return user.default_redirect
    const perms = new Set(user.permissions || [])
    if (perms.has('platform.vendors.manage')) return '/platform'
    const sales = perms.has('sales.orders.write') || perms.has('sales.orders.manage')
    const purchase = perms.has('purchase.orders.write') || perms.has('purchase.orders.manage')
    if (sales && !purchase) return '/admin/sales-orders'
    if (purchase && !sales) return '/admin/purchase-orders'
    if (sales || purchase || perms.has('dashboard.read')) return '/admin/sales-orders'
    if (perms.has('b2b.portal')) return '/b2b'
    if (vendor.storeEnabled) return '/store'
    if (user.role === 'CUSTOMER') return '/store/orders'
    return '/'
  }

  return { resolveHome }
}
