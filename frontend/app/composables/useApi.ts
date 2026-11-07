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
  // Forward browser cookies on SSR so /auth/me works on hard refresh / typed URLs
  const fetcher = import.meta.server ? useRequestFetch() : $fetch

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

    return fetcher<ApiEnvelope<T>>(url, {
      ...opts,
      credentials: 'include',
      headers
    })
  }

  return { api }
}
