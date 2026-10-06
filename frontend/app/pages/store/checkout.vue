<script setup lang="ts">
definePageMeta({ middleware: ['store-enabled', 'auth'] })

const cart = useCartStore()
const vendor = useVendorStore()
const { api } = useApi()

const address = reactive({
  street: '',
  city: '',
  state: 'TN',
  zip: '',
  phone: '',
  name: ''
})
const offerCode = ref('')
const method = ref<'COD' | 'RAZORPAY'>('COD')
const error = ref('')
const loading = ref(false)
const successCode = ref('')

const features = computed(() => vendor.vendor?.features || { cod: true, razorpay: true, reviews: true })

onMounted(() => {
  if (!cart.lines.length) navigateTo('/store')
  if (!features.value.cod && features.value.razorpay) method.value = 'RAZORPAY'
})


async function place() {
  error.value = ''
  loading.value = true
  successCode.value = ''
  const items = cart.lines.map(l => ({ item_id: l.item_id, quantity: l.quantity }))
  const body = { items, address, offer_code: offerCode.value || null }
  try {
    if (method.value === 'COD') {
      const res = await api<{ order_code: string }>('/store/checkout/cod', {
        method: 'POST',
        body
      })
      successCode.value = res.data.order_code
      cart.clear()
    } else {
      const created = await api<{
        order_code: string
        razorpay_order_id: string
        amount: number
        key_id: string
        mock: boolean
      }>('/store/checkout/razorpay/create', { method: 'POST', body })

      if (created.data.mock) {
        const paymentId = `pay_ui_${Date.now()}`
        const sig = await api<{ signature: string }>(
          `/store/checkout/razorpay/mock-sign?order_id=${encodeURIComponent(created.data.razorpay_order_id)}&payment_id=${paymentId}`
        )
        await api('/store/checkout/razorpay/verify', {
          method: 'POST',
          body: {
            order_code: created.data.order_code,
            razorpay_order_id: created.data.razorpay_order_id,
            razorpay_payment_id: paymentId,
            razorpay_signature: sig.data.signature
          }
        })
        successCode.value = created.data.order_code
        cart.clear()
      } else {
        error.value = 'Live Razorpay Checkout.js is not wired in this build — set RAZORPAY_MOCK or integrate Checkout.js.'
      }
    }
  } catch (e: unknown) {
    error.value = (e as { data?: { message?: string } })?.data?.message || 'Checkout failed'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="mx-auto max-w-lg px-4 py-10 sm:px-6">
    <h1 class="font-display text-4xl text-ink">
      Checkout
    </h1>
    <p class="mt-2 text-ink-muted">
      {{ cart.count }} items · ₹{{ cart.subtotal.toFixed(0) }}
    </p>

    <div
      v-if="successCode"
      class="mt-10 space-y-4"
    >
      <p class="text-lg text-ink">
        Order placed: <strong>{{ successCode }}</strong>
      </p>
      <UButton to="/store/orders">
        View my orders
      </UButton>
    </div>

    <form
      v-else
      class="mt-8 space-y-4"
      @submit.prevent="place"
    >
      <UFormField label="Name">
        <UInput
          v-model="address.name"
          size="lg"
          class="w-full"
        />
      </UFormField>
      <UFormField label="Street">
        <UInput
          v-model="address.street"
          size="lg"
          class="w-full"
        />
      </UFormField>
      <div class="grid grid-cols-2 gap-3">
        <UFormField label="City">
          <UInput
            v-model="address.city"
            size="lg"
            class="w-full"
          />
        </UFormField>
        <UFormField label="PIN">
          <UInput
            v-model="address.zip"
            size="lg"
            class="w-full"
          />
        </UFormField>
      </div>
      <UFormField label="State">
        <UInput
          v-model="address.state"
          size="lg"
          class="w-full"
        />
      </UFormField>
      <UFormField label="Offer code">
        <UInput
          v-model="offerCode"
          size="lg"
          class="w-full"
          placeholder="Optional"
        />
      </UFormField>

      <fieldset class="space-y-2">
        <legend class="text-sm font-medium text-ink">
          Payment
        </legend>
        <label
          v-if="features.cod"
          class="flex items-center gap-2"
        >
          <input
            v-model="method"
            type="radio"
            value="COD"
          >
          Cash on delivery
        </label>
        <label
          v-if="features.razorpay"
          class="flex items-center gap-2"
        >
          <input
            v-model="method"
            type="radio"
            value="RAZORPAY"
          >
          UPI / Razorpay
        </label>
      </fieldset>

      <p
        v-if="error"
        class="text-sm text-red-700"
      >
        {{ error }}
      </p>

      <UButton
        type="submit"
        size="xl"
        block
        :loading="loading"
      >
        Place order
      </UButton>
    </form>
  </div>
</template>
