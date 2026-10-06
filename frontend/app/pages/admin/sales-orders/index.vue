<script setup lang="ts">
definePageMeta({ layout: 'admin', middleware: ['admin'] })

const auth = useAuthStore()
const { api } = useApi()
const { data, refresh, status } = await useAdminAsyncData('admin-so', () =>
  api<{ data: Array<Record<string, unknown>> }>('/sale-orders?page_size=100')
)
const rows = computed(() => data.value?.data?.data || [])
const canWrite = computed(() => auth.hasPermission('sales.orders.write'))
</script>

<template>
  <AdminPage
    title="Sales orders"
    description="Counter and ecommerce sales"
  >
    <template #actions>
      <UButton
        v-if="canWrite"
        to="/admin/sales-orders/new"
      >
        New sale
      </UButton>
    </template>

    <p
      v-if="status === 'pending'"
      class="text-ink-muted"
    >
      Loading…
    </p>

    <!-- Desktop table -->
    <div class="hidden overflow-x-auto md:block">
      <table class="w-full text-left text-sm">
        <thead class="border-b border-gold-300 text-ink-muted">
          <tr>
            <th class="py-2 pr-3 font-medium">
              Code
            </th>
            <th class="py-2 pr-3 font-medium">
              Date
            </th>
            <th class="py-2 pr-3 font-medium">
              Status
            </th>
            <th class="py-2 pr-3 font-medium">
              Payment
            </th>
            <th class="py-2 pr-3 text-right font-medium">
              Total
            </th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="r in rows"
            :key="String(r.id)"
            class="border-b border-gold-300/50"
          >
            <td class="py-3 pr-3">
              <NuxtLink
                :to="`/admin/sales-orders/${r.id}`"
                class="font-medium text-gold-800 hover:underline"
              >
                {{ r.order_code }}
              </NuxtLink>
            </td>
            <td class="py-3 pr-3">
              {{ r.order_date }}
            </td>
            <td class="py-3 pr-3">
              {{ r.status }}
            </td>
            <td class="py-3 pr-3">
              {{ r.payment_status }}
            </td>
            <td class="py-3 text-right tabular-nums">
              ₹{{ Number(r.total_order_value).toFixed(0) }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Mobile cards -->
    <ul class="divide-y divide-gold-300/60 border-y border-gold-300/60 md:hidden">
      <li
        v-for="r in rows"
        :key="String(r.id)"
        class="py-3"
      >
        <NuxtLink
          :to="`/admin/sales-orders/${r.id}`"
          class="block"
        >
          <div class="flex justify-between gap-2">
            <span class="font-medium">{{ r.order_code }}</span>
            <span>₹{{ Number(r.total_order_value).toFixed(0) }}</span>
          </div>
          <p class="mt-1 text-sm text-ink-muted">
            {{ r.order_date }} · {{ r.status }} · {{ r.payment_status }}
          </p>
        </NuxtLink>
      </li>
    </ul>

    <p
      v-if="status !== 'pending' && !rows.length"
      class="mt-6 text-ink-muted"
    >
      No sales orders yet.
      <button
        class="text-gold-800 underline"
        type="button"
        @click="refresh()"
      >
        Refresh
      </button>
    </p>
  </AdminPage>
</template>
