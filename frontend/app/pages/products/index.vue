<script setup lang="ts">
const { api } = useApi()
const vendor = useVendorStore()
const q = ref('')

const { data, refresh, status } = await useAsyncData('products', () =>
  api<{
    data: Array<{
      id: number
      name: string
      description?: string
      sale_price: number
      is_online_sale?: boolean
      primary_image?: string | null
    }>
    store_enabled: boolean
  }>(`/public/products?page_size=48${q.value ? `&search=${encodeURIComponent(q.value)}` : ''}`)
)

const products = computed(() => data.value?.data?.data || [])

async function search() {
  await refresh()
}
</script>

<template>
  <div class="mx-auto max-w-6xl px-4 py-10 sm:px-6 sm:py-14">
    <div class="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
      <div>
        <h1 class="font-display text-4xl text-ink">
          Products
        </h1>
        <p class="mt-2 text-ink-muted">
          Browse {{ vendor.brandName }} product information.
        </p>
      </div>
      <form
        class="flex w-full max-w-sm gap-2"
        @submit.prevent="search"
      >
        <UInput
          v-model="q"
          placeholder="Search"
          class="flex-1"
          size="lg"
        />
        <UButton
          type="submit"
          size="lg"
        >
          Search
        </UButton>
      </form>
    </div>

    <p
      v-if="status === 'pending'"
      class="mt-10 text-ink-muted"
    >
      Loading…
    </p>

    <ul class="mt-10 grid gap-x-8 gap-y-10 sm:grid-cols-2 lg:grid-cols-3">
      <li
        v-for="p in products"
        :key="p.id"
      >
        <NuxtLink
          :to="`/products/${p.id}`"
          class="block space-y-3"
        >
          <div class="aspect-[4/3] overflow-hidden bg-gradient-to-br from-gold-300 to-gold-500/80">
            <img
              v-if="p.primary_image"
              :src="p.primary_image"
              :alt="p.name"
              class="h-full w-full object-cover"
            >
          </div>
          <div>
            <h2 class="font-display text-xl text-ink">
              {{ p.name }}
            </h2>
            <p class="mt-1 line-clamp-2 text-sm text-ink-muted">
              {{ p.description || 'View details' }}
            </p>
            <p class="mt-2 text-sm font-semibold text-gold-800">
              ₹{{ Number(p.sale_price).toFixed(0) }}
            </p>
          </div>
        </NuxtLink>
      </li>
    </ul>

    <p
      v-if="status !== 'pending' && !products.length"
      class="mt-12 text-ink-muted"
    >
      No products found.
    </p>
  </div>
</template>
