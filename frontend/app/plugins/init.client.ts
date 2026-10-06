export default defineNuxtPlugin(async () => {
  const vendor = useVendorStore()
  const auth = useAuthStore()
  const cart = useCartStore()
  cart.hydrate()
  await Promise.all([vendor.fetchVendor(), auth.fetchMe()])
})
