<script setup lang="ts">
definePageMeta({ middleware: ['store-enabled'] })

const { api } = useApi()
const cart = useCartStore()
const vendor = useVendorStore()

const { data, status } = await useAsyncData('store-products', () =>
  api<{
    data: Array<{
      id: number
      name: string
      sale_price: number
      available_qty: number
      primary_image?: string | null
      description?: string
    }>
  }>('/store/products?page_size=48')
)

const products = computed(() => data.value?.data?.data || [])

function add(p: { id: number, name: string, sale_price: number, primary_image?: string | null }) {
  cart.add({
    item_id: p.id,
    name: p.name,
    sale_price: Number(p.sale_price),
    primary_image: p.primary_image
  })
}
</script>

<template>
  <div class="mx-auto max-w-6xl px-4 py-10 sm:px-6">
    <div class="flex flex-wrap items-end justify-between gap-4">
      <div>
        <p class="text-sm uppercase tracking-[0.2em] text-gold-800">
          Store
        </p>
        <h1 class="font-display mt-1 text-4xl text-ink">
          {{ vendor.brandName }}
        </h1>
        <p class="mt-2 text-ink-muted">
          Online catalog — cart & checkout
        </p>
      </div>
      <UButton
        to="/store/cart"
        size="lg"
        trailing-icon="i-lucide-arrow-right"
      >
        Cart ({{ cart.count }})
      </UButton>
    </div>

    <p
      v-if="status === 'pending'"
      class="mt-10 text-ink-muted"
    >
      Loading store…
    </p>

    <ul class="mt-10 grid gap-8 sm:grid-cols-2 lg:grid-cols-3">
      <li
        v-for="p in products"
        :key="p.id"
        class="flex flex-col"
      >
        <NuxtLink
          :to="`/products/${p.id}`"
          class="aspect-[4/3] bg-gradient-to-br from-gold-300 to-gold-600"
        >
          <img
            v-if="p.primary_image"
            :src="p.primary_image"
            :alt="p.name"
            class="h-full w-full object-cover"
          >
        </NuxtLink>
        <h2 class="font-display mt-3 text-xl text-ink">
          {{ p.name }}
        </h2>
        <p class="mt-1 text-sm text-ink-muted">
          ₹{{ Number(p.sale_price).toFixed(0) }}
          <span v-if="p.available_qty != null"> · {{ p.available_qty }} in stock</span>
        </p>
        <UButton
          class="mt-3 self-start"
          size="md"
          :disabled="p.available_qty === 0"
          @click="add(p)"
        >
          Add to cart
        </UButton>
      </li>
    </ul>

    <p
      v-if="status !== 'pending' && !products.length"
      class="mt-12 text-ink-muted"
    >
      No online products yet. Mark items as online sale in admin.
    </p>
  </div>
</template>
