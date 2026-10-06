<script setup lang="ts">
const route = useRoute()
const vendor = useVendorStore()
const cart = useCartStore()
const { api } = useApi()
const id = computed(() => Number(route.params.id))

const { data, error } = await useAsyncData(() => `product-${id.value}`, () =>
  api<{
    id: number
    name: string
    description?: string
    sale_price: number
    is_online_sale?: boolean
    primary_image?: string | null
    store_enabled: boolean
    images?: Array<{ path: string }>
  }>(`/public/products/${id.value}`)
)

const product = computed(() => data.value?.data)

function addToCart() {
  if (!product.value) return
  cart.add({
    item_id: product.value.id,
    name: product.value.name,
    sale_price: Number(product.value.sale_price),
    primary_image: product.value.primary_image
  })
  navigateTo('/store/cart')
}
</script>

<template>
  <div class="mx-auto max-w-6xl px-4 py-10 sm:px-6 sm:py-14">
    <UButton
      to="/products"
      variant="ghost"
      color="neutral"
      icon="i-lucide-arrow-left"
      class="mb-6"
    >
      Products
    </UButton>

    <p
      v-if="error"
      class="text-red-700"
    >
      Product not found.
    </p>

    <div
      v-else-if="product"
      class="grid gap-10 lg:grid-cols-2 lg:gap-16"
    >
      <div class="aspect-square bg-gradient-to-br from-gold-300 via-gold-500 to-gold-700">
        <img
          v-if="product.primary_image || product.images?.[0]?.path"
          :src="product.primary_image || product.images?.[0]?.path"
          :alt="product.name"
          class="h-full w-full object-cover"
        >
      </div>
      <div>
        <p class="text-sm uppercase tracking-[0.2em] text-gold-800">
          {{ vendor.brandName }}
        </p>
        <h1 class="font-display mt-2 text-4xl text-ink sm:text-5xl">
          {{ product.name }}
        </h1>
        <p class="mt-4 text-2xl font-semibold text-gold-800">
          ₹{{ Number(product.sale_price).toFixed(0) }}
        </p>
        <p class="mt-6 max-w-prose leading-relaxed text-ink-muted whitespace-pre-line">
          {{ product.description || 'Details coming soon.' }}
        </p>

        <div class="mt-10 flex flex-wrap gap-3">
          <UButton
            v-if="vendor.storeEnabled && product.is_online_sale"
            size="xl"
            @click="addToCart"
          >
            Add to Store cart
          </UButton>
          <UButton
            v-else-if="vendor.storeEnabled"
            to="/store"
            size="xl"
            variant="outline"
          >
            Visit Store
          </UButton>
          <UButton
            v-else
            to="/contact"
            size="xl"
            variant="outline"
            color="neutral"
          >
            Enquire
          </UButton>
        </div>
      </div>
    </div>
  </div>
</template>
