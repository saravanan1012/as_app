<script setup lang="ts">
definePageMeta({ middleware: ['store-enabled', 'auth'] })

const cart = useCartStore()
const vendor = useVendorStore()
const auth = useAuthStore()
const { api } = useApi()
const { openCheckout } = useRazorpayCheckout()

const address = reactive({
  street: '',
  city: '',
  state: 'TN',
  zip: '',
  phone: '',
  name: ''
})
const offerCode = ref('')
const agreePolicies = ref(false)
const error = ref('')
const loading = ref(false)
const successCode = ref('')
const hasSavedAddress = ref(false)
const editingAddress = ref(true)

type CartPreview = {
  subtotal: number
  discount: number
  shipping_charge: number
  handling_charge: number
  total: number
  free_shipping_applied?: boolean
  gst_enabled?: boolean
  same_state?: boolean
  taxable?: number
  gst_amount?: number
  cgst_amount?: number
  sgst_amount?: number
  igst_amount?: number
  vendor_state?: string
  place_state?: string
  prices_include_gst?: boolean
  delivery_zone?: string
  delivery_eta_min?: number
  delivery_eta_max?: number
  pin_resolved?: boolean
  pin_unknown?: boolean
  shipping_rules?: {
    enabled: boolean
    flat_rate: number
    interstate_flat_rate?: number
    free_over_enabled: boolean
    free_over: number | null
  }
}

const preview = ref<CartPreview | null>(null)
const previewError = ref('')
const pinLookupError = ref('')
const pinLookupPending = ref(false)
let pinLookupSeq = 0

async function refreshPreview() {
  previewError.value = ''
  if (!cart.lines.length) {
    preview.value = null
    return
  }
  try {
    const res = await api<CartPreview>('/store/cart/preview', {
      method: 'POST',
      body: {
        items: cart.lines.map(l => ({ item_id: l.item_id, quantity: l.quantity })),
        offer_code: offerCode.value.trim() || null,
        address: {
          street: address.street || null,
          city: address.city || null,
          state: (address.state || 'TN').trim().toUpperCase().slice(0, 2) || 'TN',
          zip: address.zip || null,
          phone: address.phone || null,
          name: address.name || null
        }
      }
    })
    preview.value = res.data
  } catch (e: unknown) {
    preview.value = null
    previewError.value
      = (e as { data?: { message?: string } })?.data?.message || 'Could not calculate totals'
  }
}

const shippingHint = computed(() => {
  const rules = preview.value?.shipping_rules
  if (!rules?.enabled) return 'No delivery charge configured for Online Store.'
  if (preview.value?.free_shipping_applied || (preview.value && preview.value.shipping_charge === 0 && rules.free_over_enabled)) {
    if (rules.free_over_enabled && rules.free_over != null) {
      return `Free delivery on orders of ₹${Number(rules.free_over).toFixed(0)} or more.`
    }
    return 'Free delivery on this order.'
  }
  if (rules.free_over_enabled && rules.free_over != null) {
    const need = Math.max(0, Number(rules.free_over) - Number(preview.value?.subtotal || 0) + Number(preview.value?.discount || 0))
    if (need > 0) {
      return `Add ₹${need.toFixed(0)} more for free delivery (above ₹${Number(rules.free_over).toFixed(0)}).`
    }
  }
  const zone = preview.value?.delivery_zone
  const rate = zone === 'other_state'
    ? Number(rules.interstate_flat_rate ?? rules.flat_rate ?? 0)
    : Number(rules.flat_rate || 0)
  return zone === 'other_state'
    ? `Interstate delivery ₹${rate.toFixed(0)}`
    : `Delivery ₹${rate.toFixed(0)}`
})

const deliveryEtaLabel = computed(() => {
  const lo = preview.value?.delivery_eta_min
  const hi = preview.value?.delivery_eta_max
  if (lo == null || hi == null) return ''
  if (lo === hi) return `Est. delivery ${lo} day${lo === 1 ? '' : 's'}`
  return `Est. delivery ${lo}–${hi} days`
})

async function lookupPinState(zip: string) {
  const digits = String(zip || '').replace(/\D/g, '')
  pinLookupError.value = ''
  if (digits.length !== 6) {
    return
  }
  const seq = ++pinLookupSeq
  pinLookupPending.value = true
  try {
    const res = await api<{
      pin: string
      state_code: string | null
      state_name: string | null
    }>(`/store/pincode/${encodeURIComponent(digits)}`)
    if (seq !== pinLookupSeq) return
    const code = res.data?.state_code
    if (code) {
      address.state = code
      pinLookupError.value = ''
    } else {
      pinLookupError.value = 'Could not detect state from PIN — please confirm state.'
    }
  } catch {
    if (seq !== pinLookupSeq) return
    pinLookupError.value = 'Could not detect state from PIN — please confirm state.'
  } finally {
    if (seq === pinLookupSeq) pinLookupPending.value = false
  }
}

const { data: savedAddrRes } = await useAsyncData('checkout-shipping-address', () =>
  api<{
    street?: string | null
    city?: string | null
    state?: string | null
    zip?: string | null
    phone?: string | null
    name?: string | null
    saved?: boolean
  }>('/store/shipping-address')
)

function applySavedAddress() {
  const a = savedAddrRes.value?.data
  if (!a) return
  if (a.name) address.name = a.name
  else if (auth.user?.name) address.name = auth.user.name
  if (a.street) address.street = a.street
  if (a.city) address.city = a.city
  if (a.state) address.state = a.state
  if (a.zip) address.zip = a.zip
  if (a.phone) address.phone = a.phone
  hasSavedAddress.value = !!a.saved
  // Collapse form when we already have a usable saved address
  editingAddress.value = !a.saved
}

applySavedAddress()

onMounted(() => {
  if (!cart.lines.length) navigateTo('/store')
  void refreshPreview()
})

watch(
  [
    () => cart.lines.map(l => `${l.item_id}:${l.quantity}`).join('|'),
    offerCode,
    () => address.state,
    () => address.zip
  ],
  () => {
    void refreshPreview()
  }
)

watch(
  () => address.zip,
  (zip) => {
    void lookupPinState(zip)
  }
)

if (address.zip) {
  void lookupPinState(address.zip)
}

const addressSummary = computed(() => {
  const parts = [address.name, address.street, address.city, address.zip, address.state, address.phone]
    .map(s => (s || '').trim())
    .filter(Boolean)
  return parts.join(', ')
})

async function place() {
  error.value = ''
  if (!agreePolicies.value) {
    error.value = 'Please agree to the Terms, Privacy Policy, and Refund Policy to continue.'
    return
  }
  if (!address.street.trim() || !address.city.trim() || !address.zip.trim()) {
    error.value = 'Please enter a complete shipping address (street, city, PIN).'
    editingAddress.value = true
    return
  }
  loading.value = true
  successCode.value = ''
  const items = cart.lines.map(l => ({ item_id: l.item_id, quantity: l.quantity }))
  const body = { items, address, offer_code: offerCode.value || null }
  try {
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
      if (!created.data.key_id) {
        throw new Error(
          'Razorpay is not configured. Set RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET (test keys), set RAZORPAY_MOCK=false, then restart the API.'
        )
      }
      const payment = await openCheckout({
        key: created.data.key_id,
        orderId: created.data.razorpay_order_id,
        amount: created.data.amount,
        name: vendor.brandName,
        description: `Order ${created.data.order_code}`,
        prefillEmail: auth.user?.email || '',
        prefillName: address.name || auth.user?.name || '',
        prefillContact: address.phone || ''
      })
      await api('/store/checkout/razorpay/verify', {
        method: 'POST',
        body: {
          order_code: created.data.order_code,
          razorpay_order_id: payment.razorpay_order_id,
          razorpay_payment_id: payment.razorpay_payment_id,
          razorpay_signature: payment.razorpay_signature
        }
      })
      successCode.value = created.data.order_code
      cart.clear()
    }
  } catch (e: unknown) {
    const msg
      = e instanceof Error
        ? e.message
        : (e as { data?: { message?: string } })?.data?.message
    error.value = msg || 'Checkout failed'
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
      {{ cart.count }} items
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
      <div class="space-y-3">
        <div class="flex flex-wrap items-center justify-between gap-2">
          <p class="text-sm font-medium text-ink">
            Shipping address
          </p>
          <button
            v-if="hasSavedAddress || !editingAddress"
            type="button"
            class="text-sm text-gold-800 underline-offset-2 hover:underline"
            @click="editingAddress = !editingAddress"
          >
            {{ editingAddress ? 'Use saved summary' : 'Edit address' }}
          </button>
        </div>

        <div
          v-if="!editingAddress && hasSavedAddress"
          class="rounded-lg border border-gold-300/50 bg-gold-100/40 px-4 py-3 text-sm leading-relaxed text-ink"
        >
          {{ addressSummary }}
        </div>

        <div
          v-else
          class="space-y-4"
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
                maxlength="6"
                inputmode="numeric"
                @blur="lookupPinState(address.zip)"
              />
            </UFormField>
          </div>
          <p
            v-if="pinLookupError || preview?.pin_unknown"
            class="text-xs text-amber-800"
          >
            {{ pinLookupError || 'Could not detect state from PIN — please confirm state.' }}
          </p>
          <UFormField label="State">
            <UInput
              v-model="address.state"
              size="lg"
              class="w-full"
            />
          </UFormField>
          <UFormField label="Phone">
            <UInput
              v-model="address.phone"
              size="lg"
              class="w-full"
            />
          </UFormField>
        </div>
      </div>

      <UFormField label="Offer code">
        <UInput
          v-model="offerCode"
          size="lg"
          class="w-full"
          placeholder="Optional"
          @blur="refreshPreview"
        />
      </UFormField>

      <div class="rounded-lg border border-gold-300/50 bg-gold-100/30 px-4 py-3 text-sm text-ink">
        <p class="text-xs uppercase tracking-[0.15em] text-gold-800">
          Order summary
        </p>
        <dl class="mt-3 space-y-2">
          <div class="flex justify-between gap-4">
            <dt class="text-ink-muted">
              Items
            </dt>
            <dd>₹{{ Number(preview?.subtotal ?? cart.subtotal).toFixed(0) }}</dd>
          </div>
          <div
            v-if="Number(preview?.discount || 0) > 0"
            class="flex justify-between gap-4"
          >
            <dt class="text-ink-muted">
              Discount
            </dt>
            <dd>−₹{{ Number(preview?.discount || 0).toFixed(0) }}</dd>
          </div>
          <template v-if="preview?.gst_enabled">
            <div class="flex justify-between gap-4">
              <dt class="text-ink-muted">
                Taxable value
              </dt>
              <dd>₹{{ Number(preview.taxable || 0).toFixed(2) }}</dd>
            </div>
            <template v-if="preview.same_state">
              <div
                v-if="Number(preview.cgst_amount || 0) > 0"
                class="flex justify-between gap-4"
              >
                <dt class="text-ink-muted">
                  CGST
                </dt>
                <dd>₹{{ Number(preview.cgst_amount || 0).toFixed(2) }}</dd>
              </div>
              <div
                v-if="Number(preview.sgst_amount || 0) > 0"
                class="flex justify-between gap-4"
              >
                <dt class="text-ink-muted">
                  SGST
                </dt>
                <dd>₹{{ Number(preview.sgst_amount || 0).toFixed(2) }}</dd>
              </div>
            </template>
            <div
              v-else-if="Number(preview.igst_amount || 0) > 0"
              class="flex justify-between gap-4"
            >
              <dt class="text-ink-muted">
                IGST
              </dt>
              <dd>₹{{ Number(preview.igst_amount || 0).toFixed(2) }}</dd>
            </div>
            <p
              v-if="preview.prices_include_gst"
              class="text-xs text-ink-muted"
            >
              Prices include GST · ship to {{ preview.place_state || address.state }}
              ({{ preview.same_state ? 'intra-state' : 'inter-state' }})
            </p>
          </template>
          <div class="flex justify-between gap-4">
            <dt class="text-ink-muted">
              Delivery
            </dt>
            <dd class="text-right">
              <template v-if="preview && Number(preview.shipping_charge) === 0">
                <span
                  v-if="Number(
                    (preview.delivery_zone === 'other_state'
                      ? preview.shipping_rules?.interstate_flat_rate
                      : preview.shipping_rules?.flat_rate) || 0
                  ) > 0"
                  class="mr-2 text-ink-muted line-through"
                >₹{{ Number(
                  (preview.delivery_zone === 'other_state'
                    ? preview.shipping_rules?.interstate_flat_rate
                    : preview.shipping_rules?.flat_rate) || 0
                ).toFixed(0) }}</span>
                <span class="font-medium text-ink">₹0</span>
              </template>
              <template v-else>
                ₹{{ Number(preview?.shipping_charge ?? 0).toFixed(0) }}
              </template>
            </dd>
          </div>
          <div class="flex justify-between gap-4 border-t border-gold-300/40 pt-2 text-base font-semibold">
            <dt>Total</dt>
            <dd>₹{{ Number(preview?.total ?? cart.subtotal).toFixed(0) }}</dd>
          </div>
        </dl>
        <p
          v-if="deliveryEtaLabel"
          class="mt-2 text-xs text-ink"
        >
          {{ deliveryEtaLabel }}
        </p>
        <p class="mt-1 text-xs text-ink-muted">
          {{ shippingHint }}
        </p>
        <p
          v-if="previewError"
          class="mt-1 text-xs text-red-700"
        >
          {{ previewError }}
        </p>
      </div>

      <p class="text-sm text-ink-muted">
        Payment via <span class="font-medium text-ink">Razorpay</span> (UPI / cards).
      </p>

      <label class="flex items-start gap-2 text-sm text-ink-muted">
        <input
          v-model="agreePolicies"
          type="checkbox"
          class="mt-1"
        >
        <span>
          I agree to the
          <NuxtLink
            to="/terms"
            class="text-gold-800 underline"
            target="_blank"
          >Terms</NuxtLink>,
          <NuxtLink
            to="/privacy"
            class="text-gold-800 underline"
            target="_blank"
          >Privacy Policy</NuxtLink>, and
          <NuxtLink
            to="/refund"
            class="text-gold-800 underline"
            target="_blank"
          >Refund Policy</NuxtLink>.
        </span>
      </label>

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
        :disabled="!agreePolicies"
      >
        Pay with Razorpay
      </UButton>
    </form>
  </div>
</template>
