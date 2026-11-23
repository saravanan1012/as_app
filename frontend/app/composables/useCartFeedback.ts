/** Toast + stock-aware helpers for store cart actions. */
export function useCartFeedback() {
  const cart = useCartStore()
  const toast = useToast()

  function notifyAdded(name: string) {
    toast.add({
      title: 'Added to cart',
      description: name,
      icon: 'i-lucide-shopping-cart',
      color: 'success'
    })
  }

  function notifyOutOfStock(name?: string) {
    toast.add({
      title: 'Out of stock',
      description: name ? `${name} is currently unavailable.` : 'This item is currently unavailable.',
      icon: 'i-lucide-package-x',
      color: 'warning'
    })
  }

  function notifyStockLimit(name: string, available: number) {
    toast.add({
      title: 'Not enough stock',
      description: `${name} — only ${available} available.`,
      icon: 'i-lucide-package-x',
      color: 'warning'
    })
  }

  function tryAddToCart(
    item: {
      item_id: number
      name: string
      sale_price: number
      primary_image?: string | null
      available_qty?: number | null
    },
    qty = 1
  ): boolean {
    const available = item.available_qty
    if (available != null && available <= 0) {
      notifyOutOfStock(item.name)
      return false
    }
    const inCart = cart.lines.find(l => l.item_id === item.item_id)?.quantity || 0
    if (available != null && inCart + qty > available) {
      notifyStockLimit(item.name, available)
      return false
    }
    cart.add(
      {
        item_id: item.item_id,
        name: item.name,
        sale_price: item.sale_price,
        primary_image: item.primary_image
      },
      qty
    )
    notifyAdded(item.name)
    return true
  }

  return { tryAddToCart, notifyAdded, notifyOutOfStock, notifyStockLimit }
}
