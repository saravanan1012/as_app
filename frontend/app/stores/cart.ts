import { defineStore } from 'pinia'

export type CartLine = {
  item_id: number
  name: string
  sale_price: number
  quantity: number
  primary_image?: string | null
}

const STORAGE_KEY = 'as_cart_v1'

export const useCartStore = defineStore('cart', () => {
  const lines = ref<CartLine[]>([])

  const count = computed(() => lines.value.reduce((n, l) => n + l.quantity, 0))
  const subtotal = computed(() =>
    lines.value.reduce((n, l) => n + l.sale_price * l.quantity, 0)
  )

  function persist() {
    if (import.meta.client) {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(lines.value))
    }
  }

  function hydrate() {
    if (!import.meta.client) return
    try {
      const raw = localStorage.getItem(STORAGE_KEY)
      if (raw) lines.value = JSON.parse(raw)
    } catch {
      lines.value = []
    }
  }

  function add(item: Omit<CartLine, 'quantity'>, qty = 1) {
    const existing = lines.value.find(l => l.item_id === item.item_id)
    if (existing) existing.quantity += qty
    else lines.value.push({ ...item, quantity: qty })
    persist()
  }

  function setQty(itemId: number, quantity: number) {
    const line = lines.value.find(l => l.item_id === itemId)
    if (!line) return
    if (quantity <= 0) {
      lines.value = lines.value.filter(l => l.item_id !== itemId)
    } else {
      line.quantity = quantity
    }
    persist()
  }

  function remove(itemId: number) {
    lines.value = lines.value.filter(l => l.item_id !== itemId)
    persist()
  }

  function clear() {
    lines.value = []
    persist()
  }

  return { lines, count, subtotal, hydrate, add, setQty, remove, clear }
})
