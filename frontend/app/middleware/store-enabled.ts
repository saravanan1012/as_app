export default defineNuxtRouteMiddleware(async () => {
  const vendor = useVendorStore()
  if (!vendor.loaded) {
    await vendor.fetchVendor()
  }
  if (!vendor.storeEnabled) {
    return navigateTo('/')
  }
})
