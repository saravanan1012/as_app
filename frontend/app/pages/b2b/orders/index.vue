<script setup lang="ts">
definePageMeta({ layout: 'b2b', middleware: ['b2b'] })

const { api } = useApi()
const { data, status } = await useAsyncData('b2b-orders', () =>
  api<{ data: Array<Record<string, any>> }>('/b2b/orders')
)
const rows = computed(() => data.value?.data?.data || [])
</script>

<template>
  <div>
    <div class="flex flex-wrap items-end justify-between gap-3">
      <h1 class="font-display text-3xl">
        Orders
      </h1>
      <UButton to="/b2b/orders/new">
        New order
      </UButton>
    </div>
    <p
      v-if="status === 'pending'"
      class="mt-6 text-ink-muted"
    >
      Loading…
    </p>
    <ul
      v-else
      class="mt-6 divide-y divide-gold-300/60 border-y border-gold-300/60"
    >
      <li
        v-for="o in rows"
        :key="o.id"
      >
        <NuxtLink
          :to="`/b2b/orders/${o.id}`"
          class="flex flex-wrap items-baseline justify-between gap-2 py-4 hover:bg-gold-50/80"
        >
          <div>
            <p class="font-medium">
              {{ o.order_code }}
            </p>
            <p class="text-sm text-ink-muted">
              {{ o.order_date }} · {{ o.status }} · {{ o.fulfillment_status }}
              <span v-if="o.courier_label || o.tracking_number">
                · {{ o.courier_label || o.courier }} {{ o.tracking_number }}
              </span>
            </p>
          </div>
          <p class="font-semibold text-gold-800">
            ₹{{ Number(o.total_order_value).toFixed(0) }}
          </p>
        </NuxtLink>
      </li>
      <li
        v-if="!rows.length"
        class="py-8 text-ink-muted"
      >
        No orders yet.
      </li>
    </ul>
  </div>
</template>
