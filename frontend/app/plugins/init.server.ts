export default defineNuxtPlugin(async () => {
  const vendor = useVendorStore()
  await vendor.fetchVendor()
})
