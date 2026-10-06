export type NavItem = {
  label: string
  to: string
  permission: string
  icon: string
}

export function useAdminNav() {
  const auth = useAuthStore()

  const items: NavItem[] = [
    { label: 'Dashboard', to: '/admin', permission: 'dashboard.read', icon: 'i-lucide-layout-dashboard' },
    { label: 'Sales', to: '/admin/sales-orders', permission: 'sales.orders.read', icon: 'i-lucide-receipt' },
    { label: 'Purchase', to: '/admin/purchase-orders', permission: 'purchase.orders.read', icon: 'i-lucide-truck' },
    { label: 'Items', to: '/admin/items', permission: 'catalog.items.read', icon: 'i-lucide-package' },
    { label: 'Stock', to: '/admin/stock', permission: 'stock.read', icon: 'i-lucide-warehouse' },
    { label: 'Customers', to: '/admin/customers', permission: 'customers.read', icon: 'i-lucide-users' },
    { label: 'Suppliers', to: '/admin/suppliers', permission: 'suppliers.read', icon: 'i-lucide-factory' },
    { label: 'Shipping', to: '/admin/shipping', permission: 'customers.manage', icon: 'i-lucide-package-check' },
    { label: 'Offers', to: '/admin/offers', permission: 'offers.read', icon: 'i-lucide-ticket-percent' },
    { label: 'Transactions', to: '/admin/transactions', permission: 'transactions.read', icon: 'i-lucide-wallet' },
    { label: 'Users', to: '/admin/users', permission: 'users.read', icon: 'i-lucide-user-cog' },
    { label: 'Audit', to: '/admin/audit', permission: 'audit.read', icon: 'i-lucide-scroll-text' }
  ]

  const visible = computed(() => items.filter(i => auth.hasPermission(i.permission)))

  return { items, visible }
}
