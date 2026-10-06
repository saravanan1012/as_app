import { defineStore } from 'pinia'

/** Super-admin acting vendor for /admin APIs (?vendor_id=). */
export const useAdminContextStore = defineStore('adminContext', () => {
  const vendorId = ref<number | null>(null)

  function hydrate() {
    if (!import.meta.client) return
    const raw = sessionStorage.getItem('as_acting_vendor_id')
    if (raw && /^\d+$/.test(raw)) vendorId.value = Number(raw)
  }

  function setVendorId(id: number | null) {
    vendorId.value = id
    if (import.meta.client) {
      if (id) sessionStorage.setItem('as_acting_vendor_id', String(id))
      else sessionStorage.removeItem('as_acting_vendor_id')
    }
  }

  return { vendorId, hydrate, setVendorId }
})
