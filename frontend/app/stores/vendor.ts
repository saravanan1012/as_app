import { defineStore } from 'pinia'

export type VendorPublic = {
  vendor_id: number
  slug: string
  name: string
  legal_name?: string | null
  address?: string | null
  store_enabled: boolean
  branding: {
    logo_url: string
    primary: string
    theme_id: string
    store_name: string
    company_blurb: string
    company_tagline: string
  }
  features: {
    cod: boolean
    razorpay: boolean
    reviews: boolean
  }
  currency: string
}

export const useVendorStore = defineStore('vendor', () => {
  const config = useRuntimeConfig()
  const slug = ref(config.public.vendorSlug as string)
  const vendor = ref<VendorPublic | null>(null)
  const loaded = ref(false)
  const error = ref<string | null>(null)

  const storeEnabled = computed(() => !!vendor.value?.store_enabled)
  const brandName = computed(
    () => vendor.value?.branding.store_name || vendor.value?.name || 'AS Organic'
  )
  const tagline = computed(() => vendor.value?.branding.company_tagline || '')
  const blurb = computed(() => vendor.value?.branding.company_blurb || '')

  async function fetchVendor() {
    error.value = null
    try {
      const { api } = useApi()
      const res = await api<VendorPublic>('/public/vendor')
      vendor.value = res.data
      if (res.data.slug) slug.value = res.data.slug
      if (res.data.branding?.primary) {
        document.documentElement.style.setProperty('--ui-primary', res.data.branding.primary)
      }
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : 'Failed to load vendor'
    } finally {
      loaded.value = true
    }
  }

  return {
    slug,
    vendor,
    loaded,
    error,
    storeEnabled,
    brandName,
    tagline,
    blurb,
    fetchVendor
  }
})
