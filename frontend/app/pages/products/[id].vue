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

const { data: reviewsRes } = await useAsyncData(
  () => `product-reviews-${id.value}`,
  async () => {
    if (!vendor.storeEnabled) return null
    try {
      return await api<Array<{
        id: number
        rating: number
        comment?: string | null
        is_verified_purchase?: boolean
        created_at?: string
      }>>(`/store/products/${id.value}/reviews`)
    } catch {
      return null
    }
  }
)

const reviews = computed(() => reviewsRes.value?.data || [])
const avgRating = computed(() => {
  if (!reviews.value.length) return null
  const sum = reviews.value.reduce((acc, r) => acc + Number(r.rating || 0), 0)
  return sum / reviews.value.length
})

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

function stars(n: number | null) {
  if (n == null) return ''
  const full = Math.round(n)
  return '★'.repeat(full) + '☆'.repeat(Math.max(0, 5 - full))
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
      <ProductImageSlider
        :images="product.images || []"
        :primary="product.primary_image"
        :alt="product.name"
      />
      <div>
        <p class="text-sm uppercase tracking-[0.2em] text-gold-800">
          {{ vendor.brandName }}
        </p>
        <h1 class="font-display mt-2 text-4xl text-ink sm:text-5xl">
          {{ product.name }}
        </h1>
        <p
          v-if="avgRating != null"
          class="mt-3 flex flex-wrap items-center gap-2 text-gold-800"
        >
          <span
            class="text-lg tracking-tight"
            aria-hidden="true"
          >{{ stars(avgRating) }}</span>
          <span class="text-sm font-medium text-ink">{{ avgRating.toFixed(1) }}</span>
          <span class="text-sm text-ink-muted">({{ reviews.length }} review{{ reviews.length === 1 ? '' : 's' }})</span>
        </p>
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

        <section
          v-if="reviews.length"
          class="mt-12 border-t border-gold-300/50 pt-8"
        >
          <h2 class="font-display text-2xl text-ink">
            Customer reviews
          </h2>
          <ul class="mt-6 space-y-4">
            <li
              v-for="r in reviews"
              :key="r.id"
              class="rounded-lg border border-gold-300/40 bg-gold-100/40 px-4 py-3"
            >
              <p class="text-sm text-gold-800" aria-hidden="true">
                {{ stars(r.rating) }}
              </p>
              <p class="mt-1 text-sm leading-relaxed text-ink-muted">
                {{ r.comment || 'No comment.' }}
              </p>
              <p
                v-if="r.is_verified_purchase"
                class="mt-1 text-xs uppercase tracking-wide text-ink-muted"
              >
                Verified purchase
              </p>
            </li>
          </ul>
        </section>
      </div>
    </div>
  </div>
</template>
