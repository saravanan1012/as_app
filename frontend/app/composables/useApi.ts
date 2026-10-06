type ApiEnvelope<T> = {
  success: boolean
  message: string
  data: T
  error?: string | null
}

export function useApi() {
  const config = useRuntimeConfig()
  const vendor = useVendorStore()
  const auth = useAuthStore()
  const adminCtx = useAdminContextStore()

  async function api<T>(path: string, opts: Parameters<typeof $fetch>[1] = {}) {
    const headers: Record<string, string> = {
      ...(opts.headers as Record<string, string> | undefined),
      'x-vendor-slug': vendor.slug || config.public.vendorSlug
    }

    let url = `${config.public.apiBase}${path}`
    if (auth.user?.role === 'SUPER_ADMIN' && adminCtx.vendorId) {
      const sep = url.includes('?') ? '&' : '?'
      url = `${url}${sep}vendor_id=${adminCtx.vendorId}`
    }

    return $fetch<ApiEnvelope<T>>(url, {
      ...opts,
      credentials: 'include',
      headers
    })
  }

  return { api }
}
