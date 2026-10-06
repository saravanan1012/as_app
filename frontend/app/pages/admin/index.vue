<script setup lang="ts">
definePageMeta({ layout: 'admin', middleware: ['admin'] })

const { api } = useApi()
const { data } = await useAdminAsyncData('admin-dash', () =>
  api<{
    items: number
    customers: number
    stock_on_hand_total: number
    customers_by_party_type: Record<string, number>
  }>('/dashboard')
)

const d = computed(() => data.value?.data)
</script>

<template>
  <AdminPage
    title="Dashboard"
    description="Vendor snapshot"
  >
    <div class="grid gap-4 sm:grid-cols-3">
      <div class="border-y border-gold-300/70 py-4">
        <p class="text-sm text-ink-muted">
          Items
        </p>
        <p class="font-display text-3xl">
          {{ d?.items ?? '—' }}
        </p>
      </div>
      <div class="border-y border-gold-300/70 py-4">
        <p class="text-sm text-ink-muted">
          Customers
        </p>
        <p class="font-display text-3xl">
          {{ d?.customers ?? '—' }}
        </p>
      </div>
      <div class="border-y border-gold-300/70 py-4">
        <p class="text-sm text-ink-muted">
          Stock on hand
        </p>
        <p class="font-display text-3xl">
          {{ d?.stock_on_hand_total ?? '—' }}
        </p>
      </div>
    </div>

    <h2 class="font-display mt-10 text-xl">
      Parties
    </h2>
    <ul class="mt-3 divide-y divide-gold-300/60 border-y border-gold-300/60">
      <li
        v-for="(n, type) in d?.customers_by_party_type || {}"
        :key="type"
        class="flex justify-between py-3 text-sm"
      >
        <span>{{ type }}</span>
        <span class="font-semibold">{{ n }}</span>
      </li>
    </ul>
  </AdminPage>
</template>
