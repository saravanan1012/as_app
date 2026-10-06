<script setup lang="ts">
definePageMeta({ layout: 'admin', middleware: ['admin'] })

const auth = useAuthStore()
const { api } = useApi()
const { data, status } = await useAdminAsyncData('admin-po', () =>
  api<{ data: Array<Record<string, any>> }>('/purchase-orders?page_size=100')
)
const rows = computed(() => data.value?.data?.data || [])
</script>

<template>
  <AdminPage
    title="Purchase orders"
    description="PO + GRN receive"
  >
    <template #actions>
      <UButton
        v-if="auth.hasPermission('purchase.orders.write')"
        to="/admin/purchase-orders/new"
      >
        New PO
      </UButton>
    </template>

    <p
      v-if="status === 'pending'"
      class="text-ink-muted"
    >
      Loading…
    </p>
    <ul class="divide-y divide-gold-300/60 border-y border-gold-300/60">
      <li
        v-for="r in rows"
        :key="r.id"
        class="flex flex-wrap items-baseline justify-between gap-2 py-3"
      >
        <NuxtLink
          :to="`/admin/purchase-orders/${r.id}`"
          class="font-medium text-gold-800 hover:underline"
        >
          {{ r.order_code }}
        </NuxtLink>
        <span class="text-sm text-ink-muted">{{ r.order_date }} · {{ r.status }}</span>
        <span class="tabular-nums">₹{{ Number(r.total_purchase_cost).toFixed(0) }}</span>
      </li>
      <li
        v-if="!rows.length && status !== 'pending'"
        class="py-6 text-ink-muted"
      >
        No purchase orders.
      </li>
    </ul>
  </AdminPage>
</template>
