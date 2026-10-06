/**
 * Admin/page data loader that does not reject the route Suspense.
 * `lazy: true` mounts the page immediately so RouterView is not left mid-Suspense
 * (which surfaces as emitsOptions / parentNode null on menu clicks).
 */
export function useAdminAsyncData<T>(
  key: string | (() => string),
  handler: () => Promise<T>,
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  opts: Record<string, any> = {}
) {
  return useAsyncData<T>(key, handler, {
    lazy: true,
    ...opts,
    throw: false
  })
}
