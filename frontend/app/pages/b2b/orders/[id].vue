<script setup lang="ts">
definePageMeta({ layout: 'b2b', middleware: ['b2b'] })

const route = useRoute()
const { api } = useApi()
const vendor = useVendorStore()
const auth = useAuthStore()
const id = computed(() => Number(route.params.id))

const { data } = await useAsyncData(() => `b2b-so-${id.value}`, () =>
  api<Record<string, any>>(`/b2b/orders/${id.value}`)
)
const order = computed(() => data.value?.data)

async function downloadInvoice() {
  if (!order.value) return
  const { downloadSaleOrderInvoicePdf } = await import('~/utils/invoicePdf')
  downloadSaleOrderInvoicePdf(
    {
      companyName: vendor.brandName || 'AS Organic',
      gstin: vendor.vendor?.gstin,
      addressLines: vendor.vendor?.address ? [vendor.vendor.address] : [],
      email: auth.user?.email
    },
    { name: order.value.shipping_name },
    {
      ...order.value,
      handling_charge: order.value.handling_charge || 0,
      items: (order.value.items || []).map((l: any) => ({
        ...l,
        discount_amount: l.discount_amount || 0
      }))
    }
  )
}
</script>

<template>
  <div v-if="order">
    <div class="flex flex-wrap items-start justify-between gap-3">
      <div>
        <h1 class="font-display text-3xl">
          {{ order.order_code }}
        </h1>
        <p class="mt-1 text-ink-muted">
          {{ order.order_date }} · {{ order.status }} · {{ order.payment_status }}
        </p>
      </div>
      <UButton
        variant="outline"
        @click="downloadInvoice"
      >
        Invoice PDF
      </UButton>
    </div>

    <dl class="mt-6 grid gap-3 text-sm sm:grid-cols-2">
      <div>
        <dt class="text-ink-muted">
          Fulfillment
        </dt>
        <dd>{{ order.fulfillment_status }}</dd>
      </div>
      <div>
        <dt class="text-ink-muted">
          Total
        </dt>
        <dd class="font-semibold">
          ₹{{ Number(order.total_order_value).toFixed(2) }}
        </dd>
      </div>
      <div>
        <dt class="text-ink-muted">
          Delivery
        </dt>
        <dd>
          <template v-if="order.courier || order.tracking_number">
            {{ order.courier_label || order.courier }} · {{ order.tracking_number }}
          </template>
          <template v-else>
            Not shipped yet
          </template>
        </dd>
      </div>
    </dl>

    <h2 class="font-display mt-8 text-xl">
      Lines
    </h2>
    <ul class="mt-3 divide-y divide-gold-300/60 border-y border-gold-300/60">
      <li
        v-for="line in order.items || []"
        :key="line.id"
        class="flex justify-between gap-3 py-3 text-sm"
      >
        <div>
          <p class="font-medium">
            {{ line.item_name }}
          </p>
          <p class="text-ink-muted">
            {{ line.quantity }} × ₹{{ Number(line.unit_price).toFixed(2) }}
          </p>
        </div>
        <p>₹{{ Number(line.net_line_total).toFixed(2) }}</p>
      </li>
    </ul>
  </div>
</template>
