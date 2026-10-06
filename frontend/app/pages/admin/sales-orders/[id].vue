<script setup lang="ts">
definePageMeta({ layout: 'admin', middleware: ['admin'] })

const route = useRoute()
const { api } = useApi()
const vendor = useVendorStore()
const auth = useAuthStore()
const id = computed(() => Number(route.params.id))

const { data, refresh } = await useAdminAsyncData(() => `so-${id.value}`, () =>
  api<Record<string, any>>(`/sale-orders/${id.value}`)
)
const order = computed(() => data.value?.data)

const shipForm = reactive({
  courier: 'AKR_PARCEL',
  tracking_number: ''
})
const shipError = ref('')
const shipping = ref(false)

async function confirm() {
  await api(`/sale-orders/${id.value}/confirm`, { method: 'POST' })
  await refresh()
}
async function cancel() {
  await api(`/sale-orders/${id.value}/cancel`, {
    method: 'POST',
    body: { reason: 'Cancelled from admin' }
  })
  await refresh()
}

async function ship() {
  shipError.value = ''
  shipping.value = true
  try {
    await api(`/sale-orders/${id.value}/shipment`, {
      method: 'PATCH',
      body: { ...shipForm }
    })
    await refresh()
  } catch (e: unknown) {
    shipError.value = (e as { data?: { message?: string } })?.data?.message || 'Ship failed'
  } finally {
    shipping.value = false
  }
}

async function downloadInvoice() {
  if (!order.value) return
  let customer = null
  if (order.value.customer_id) {
    try {
      const c = await api<any>(`/customers/${order.value.customer_id}`)
      customer = {
        name: c.data.name,
        gstin: c.data.gstin,
        phone: c.data.phone,
        email: c.data.email,
        street: c.data.addresses?.[0]?.street,
        city: c.data.addresses?.[0]?.city,
        zip: c.data.addresses?.[0]?.zip,
        state: c.data.addresses?.[0]?.state
      }
    } catch { /* optional */ }
  }
  const { downloadSaleOrderInvoicePdf } = await import('~/utils/invoicePdf')
  downloadSaleOrderInvoicePdf(
    {
      companyName: vendor.brandName,
      gstin: vendor.vendor?.gstin,
      addressLines: vendor.vendor?.address ? [vendor.vendor.address] : [],
      email: auth.user?.email
    },
    customer,
    order.value as any
  )
}
</script>

<template>
  <AdminPage
    v-if="order"
    :title="String(order.order_code)"
    :description="`${order.order_date} · ${order.status}`"
  >
    <template #actions>
      <UButton
        variant="outline"
        @click="downloadInvoice"
      >
        Invoice PDF
      </UButton>
      <UButton
        v-if="order.status === 'DRAFT'"
        @click="confirm"
      >
        Confirm
      </UButton>
      <UButton
        v-if="order.status !== 'CANCELLED'"
        color="neutral"
        variant="soft"
        @click="cancel"
      >
        Cancel
      </UButton>
    </template>

    <dl class="grid gap-3 text-sm sm:grid-cols-2">
      <div>
        <dt class="text-ink-muted">
          Payment
        </dt>
        <dd>{{ order.payment_status }} · {{ order.payment_method || '—' }}</dd>
      </div>
      <div>
        <dt class="text-ink-muted">
          Channel
        </dt>
        <dd>{{ order.sales_channel }}</dd>
      </div>
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
          Tax
        </dt>
        <dd>₹{{ Number(order.total_tax_amount).toFixed(2) }}</dd>
      </div>
      <div v-if="order.courier || order.tracking_number">
        <dt class="text-ink-muted">
          Tracking
        </dt>
        <dd>
          {{ order.courier_label || order.courier }} · {{ order.tracking_number }}
        </dd>
      </div>
    </dl>

    <section
      v-if="order.status !== 'CANCELLED' && order.fulfillment_status !== 'SHIPPED'"
      class="mt-8 max-w-md space-y-3 rounded-lg border border-gold-300/60 p-4"
    >
      <h2 class="font-display text-lg">
        Ship package
      </h2>
      <UFormField label="Courier">
        <USelect
          v-model="shipForm.courier"
          :items="[
            { label: 'AKR Parcel', value: 'AKR_PARCEL' },
            { label: 'Maruthi Parcel', value: 'MARUTHI_PARCEL' }
          ]"
          class="w-full"
        />
      </UFormField>
      <UFormField label="Tracking number">
        <UInput
          v-model="shipForm.tracking_number"
          class="w-full"
          required
        />
      </UFormField>
      <p
        v-if="shipError"
        class="text-sm text-red-700"
      >
        {{ shipError }}
      </p>
      <UButton
        :loading="shipping"
        @click="ship"
      >
        Mark shipped
      </UButton>
    </section>

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
            {{ line.item_name || line.item_id }}
          </p>
          <p class="text-ink-muted">
            {{ line.quantity }} × ₹{{ Number(line.unit_price).toFixed(2) }} · GST {{ line.gst_rate }}%
            <span v-if="line.trade_unit_price != null">
              · trade ₹{{ Number(line.trade_unit_price).toFixed(2) }}
            </span>
          </p>
        </div>
        <p class="tabular-nums">
          ₹{{ Number(line.net_line_total).toFixed(2) }}
        </p>
      </li>
    </ul>
  </AdminPage>
</template>
