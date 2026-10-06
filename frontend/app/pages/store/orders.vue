<script setup lang="ts">
definePageMeta({ middleware: ['auth'] })

const { api } = useApi()
const vendor = useVendorStore()
const auth = useAuthStore()
const selectedId = ref<number | null>(null)

const { data, status, refresh } = await useAsyncData('my-orders', () =>
  api<{
    data: Array<Record<string, any>>
  }>('/store/my-orders')
)

const orders = computed(() => data.value?.data?.data || [])

const { data: detailRes, refresh: refreshDetail } = await useAsyncData(
  'my-order-detail',
  async () => {
    if (!selectedId.value) return null
    return api<Record<string, any>>(`/store/my-orders/${selectedId.value}`)
  },
  { watch: [selectedId], immediate: false }
)
const detail = computed(() => detailRes.value?.data)

async function openOrder(id: number) {
  selectedId.value = id
  await refreshDetail()
}

async function downloadInvoice() {
  if (!detail.value) return
  const { downloadSaleOrderInvoicePdf } = await import('~/utils/invoicePdf')
  downloadSaleOrderInvoicePdf(
    {
      companyName: vendor.brandName || 'AS Organic',
      gstin: vendor.vendor?.gstin,
      addressLines: vendor.vendor?.address ? [vendor.vendor.address] : [],
      email: auth.user?.email
    },
    { name: detail.value.shipping_name },
    {
      ...detail.value,
      handling_charge: detail.value.handling_charge || 0,
      items: (detail.value.items || []).map((l: any) => ({
        ...l,
        discount_amount: l.discount_amount || 0
      }))
    }
  )
}
</script>

<template>
  <div class="mx-auto max-w-2xl px-4 py-10 sm:px-6">
    <h1 class="font-display text-4xl text-ink">
      My orders
    </h1>
    <p
      v-if="status === 'pending'"
      class="mt-8 text-ink-muted"
    >
      Loading…
    </p>

    <div
      v-else-if="detail"
      class="mt-8"
    >
      <UButton
        variant="ghost"
        class="mb-4"
        @click="selectedId = null; refresh()"
      >
        ← Back
      </UButton>
      <div class="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 class="font-display text-2xl">
            {{ detail.order_code }}
          </h2>
          <p class="text-sm text-ink-muted">
            {{ detail.status }} · {{ detail.payment_status }} · {{ detail.fulfillment_status }}
          </p>
        </div>
        <UButton
          variant="outline"
          @click="downloadInvoice"
        >
          Invoice PDF
        </UButton>
      </div>
      <p class="mt-4 text-sm">
        <span class="text-ink-muted">Delivery:</span>
        <template v-if="detail.courier || detail.tracking_number">
          {{ detail.courier_label || detail.courier }} · {{ detail.tracking_number }}
        </template>
        <template v-else>
          Not shipped yet
        </template>
      </p>
      <p class="mt-2 font-semibold">
        ₹{{ Number(detail.total_order_value).toFixed(2) }}
      </p>
      <ul class="mt-6 divide-y divide-gold-300/70 border-y border-gold-300/70">
        <li
          v-for="line in detail.items || []"
          :key="line.id"
          class="flex justify-between py-3 text-sm"
        >
          <span>{{ line.item_name }} × {{ line.quantity }}</span>
          <span>₹{{ Number(line.net_line_total).toFixed(2) }}</span>
        </li>
      </ul>
    </div>

    <ul
      v-else
      class="mt-8 divide-y divide-gold-300/70 border-y border-gold-300/70"
    >
      <li
        v-for="o in orders"
        :key="o.id"
      >
        <button
          type="button"
          class="flex w-full flex-wrap items-baseline justify-between gap-2 py-4 text-left hover:bg-gold-50/50"
          @click="openOrder(o.id)"
        >
          <div>
            <p class="font-medium text-ink">
              {{ o.order_code }}
            </p>
            <p class="text-sm text-ink-muted">
              {{ o.order_date }} · {{ o.status }} · {{ o.fulfillment_status || o.payment_status }}
              <span v-if="o.courier_label || o.tracking_number">
                · {{ o.courier_label || o.courier }} {{ o.tracking_number }}
              </span>
            </p>
          </div>
          <p class="font-semibold text-gold-800">
            ₹{{ Number(o.total_order_value).toFixed(0) }}
          </p>
        </button>
      </li>
      <li
        v-if="!orders.length"
        class="py-8 text-ink-muted"
      >
        No orders yet.
      </li>
    </ul>
  </div>
</template>
