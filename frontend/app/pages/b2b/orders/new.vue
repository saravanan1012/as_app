<script setup lang="ts">
definePageMeta({ layout: 'b2b', middleware: ['b2b'] })

const { api } = useApi()
const error = ref('')
const loading = ref(false)
const customerId = ref<number | null>(null)

type CatalogItem = {
  id: number
  code: string
  name: string
  msrp: number
  trade_unit_price: number
  suggested_sell: number
  is_online_sale: boolean
}
type CartLine = { item_id: number, name: string, quantity: number, unit_price: number, trade_unit_price: number }

const cart = ref<CartLine[]>([])
const preview = ref<Record<string, any> | null>(null)

const { data: downlineRes } = await useAsyncData('b2b-dl-new', () =>
  api<{ data: Array<{ id: number, name: string, party_type: string }> }>('/b2b/downline')
)
const { data: catalogRes } = await useAsyncData('b2b-cat', () =>
  api<{ data: CatalogItem[] }>('/b2b/catalog')
)

const customers = computed(() => downlineRes.value?.data?.data || [])
const catalog = computed(() => catalogRes.value?.data?.data || [])

function addItem(it: CatalogItem) {
  const existing = cart.value.find(c => c.item_id === it.id)
  if (existing) {
    existing.quantity += 1
  } else {
    cart.value.push({
      item_id: it.id,
      name: it.name,
      quantity: 1,
      unit_price: it.suggested_sell,
      trade_unit_price: it.trade_unit_price
    })
  }
}

async function runPreview() {
  preview.value = null
  if (!customerId.value || !cart.value.length) return
  const res = await api<Record<string, any>>('/b2b/cart/preview', {
    method: 'POST',
    body: {
      customer_id: customerId.value,
      items: cart.value.map(c => ({
        item_id: c.item_id,
        quantity: c.quantity,
        unit_price: c.unit_price
      }))
    }
  })
  preview.value = res.data
}

async function place() {
  error.value = ''
  if (!customerId.value || !cart.value.length) {
    error.value = 'Pick a customer and add items'
    return
  }
  loading.value = true
  try {
    await runPreview()
    const res = await api<{ id: number }>('/b2b/orders', {
      method: 'POST',
      body: {
        customer_id: customerId.value,
        items: cart.value.map(c => ({
          item_id: c.item_id,
          quantity: c.quantity,
          unit_price: c.unit_price
        })),
        status: 'CONFIRMED',
        payment_status: 'UNPAID',
        payment_method: 'COD'
      }
    })
    await navigateTo(`/b2b/orders/${res.data.id}`)
  } catch (e: unknown) {
    error.value = (e as { data?: { message?: string } })?.data?.message || 'Order failed'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div>
    <h1 class="font-display text-3xl">
      New order
    </h1>
    <p class="mt-2 text-sm text-ink-muted">
      Customer pays sell price (trade + your profit). Sell price cannot go below your trade cost.
    </p>

    <UFormField
      label="Bill to (downline)"
      class="mt-6 max-w-md"
    >
      <USelect
        v-model="customerId"
        :items="customers.map(c => ({ label: `${c.name} (${c.party_type})`, value: c.id }))"
        class="w-full"
        placeholder="Select party"
      />
    </UFormField>

    <h2 class="font-display mt-8 text-xl">
      Catalog
    </h2>
    <ul class="mt-3 divide-y divide-gold-300/50 border-y border-gold-300/50">
      <li
        v-for="it in catalog"
        :key="it.id"
        class="flex flex-wrap items-center justify-between gap-2 py-3 text-sm"
      >
        <div>
          <p class="font-medium">
            {{ it.name }}
          </p>
          <p class="text-ink-muted">
            Trade ₹{{ it.trade_unit_price }} · MSRP ₹{{ it.msrp }}
            <span v-if="!it.is_online_sale"> · offline SKU</span>
          </p>
        </div>
        <UButton
          size="sm"
          variant="outline"
          @click="addItem(it)"
        >
          Add
        </UButton>
      </li>
    </ul>

    <h2 class="font-display mt-8 text-xl">
      Cart
    </h2>
    <ul
      v-if="cart.length"
      class="mt-3 space-y-3"
    >
      <li
        v-for="line in cart"
        :key="line.item_id"
        class="grid gap-2 rounded border border-gold-300/50 p-3 sm:grid-cols-[1fr_5rem_7rem]"
      >
        <div>
          <p class="font-medium">
            {{ line.name }}
          </p>
          <p class="text-xs text-ink-muted">
            Min trade ₹{{ line.trade_unit_price }}
          </p>
        </div>
        <UFormField label="Qty">
          <UInput
            v-model.number="line.quantity"
            type="number"
            min="1"
            class="w-full"
          />
        </UFormField>
        <UFormField label="Sell ₹">
          <UInput
            v-model.number="line.unit_price"
            type="number"
            step="0.01"
            class="w-full"
          />
        </UFormField>
      </li>
    </ul>
    <p
      v-else
      class="mt-3 text-ink-muted"
    >
      Cart empty.
    </p>

    <div class="mt-6 flex flex-wrap gap-2">
      <UButton
        variant="outline"
        @click="runPreview"
      >
        Preview totals
      </UButton>
      <UButton
        :loading="loading"
        @click="place"
      >
        Place order
      </UButton>
    </div>

    <dl
      v-if="preview"
      class="mt-4 grid max-w-sm gap-1 text-sm"
    >
      <div class="flex justify-between">
        <dt>Qty</dt>
        <dd>{{ preview.total_qty }}</dd>
      </div>
      <div class="flex justify-between">
        <dt>Subtotal</dt>
        <dd>₹{{ Number(preview.subtotal).toFixed(2) }}</dd>
      </div>
      <div class="flex justify-between">
        <dt>Tax</dt>
        <dd>₹{{ Number(preview.tax).toFixed(2) }}</dd>
      </div>
      <div class="flex justify-between">
        <dt>Shipping</dt>
        <dd>₹{{ Number(preview.shipping_charge).toFixed(2) }}</dd>
      </div>
      <div class="flex justify-between font-semibold">
        <dt>Total</dt>
        <dd>₹{{ Number(preview.total_order_value).toFixed(2) }}</dd>
      </div>
    </dl>

    <p
      v-if="error"
      class="mt-4 text-sm text-red-700"
    >
      {{ error }}
    </p>
  </div>
</template>
