<script setup lang="ts">
definePageMeta({ layout: 'admin', middleware: ['admin'] })

const auth = useAuthStore()
const { api } = useApi()

type OfferRow = Record<string, any>

const { data, refresh, status } = await useAdminAsyncData('admin-offers', () =>
  api<OfferRow[]>('/offers')
)
const rows = computed(() => data.value?.data || [])

const editingId = ref<number | null>(null)
const showForm = ref(false)

const emptyForm = () => ({
  code: '',
  description: '',
  discount_percentage: null as number | null,
  discount_amount: null as number | null,
  free_shipping: false,
  min_order_value: null as number | null,
  customer_type: 'ANY',
  sales_channel: 'ECOMMERCE',
  max_uses: null as number | null,
  max_uses_per_customer: null as number | null,
  start_date: '' as string,
  end_date: '' as string,
  is_active: true
})

const form = reactive(emptyForm())
const error = ref('')
const loading = ref(false)
const deletingId = ref<number | null>(null)

const canWrite = computed(() => auth.hasPermission('offers.write'))
const formTitle = computed(() => (editingId.value ? 'Edit offer' : 'New offer'))

const partyItems = [
  { label: 'Any party', value: 'ANY' },
  { label: 'Distributor', value: 'DISTRIBUTOR' },
  { label: 'Dealer', value: 'DEALER' },
  { label: 'Retailer', value: 'RETAILER' },
  { label: 'Customer', value: 'CUSTOMER' }
]

const channelItems = [
  { label: 'Ecommerce', value: 'ECOMMERCE' },
  { label: 'Counter', value: 'COUNTER' },
  { label: 'Any channel', value: 'ANY' }
]

function resetForm() {
  Object.assign(form, emptyForm())
  editingId.value = null
  error.value = ''
}

function openCreate() {
  resetForm()
  showForm.value = true
}

function openEdit(o: OfferRow) {
  editingId.value = o.id
  Object.assign(form, {
    code: o.code || '',
    description: o.description || '',
    discount_percentage: o.discount_percentage != null ? Number(o.discount_percentage) : null,
    discount_amount: o.discount_amount != null ? Number(o.discount_amount) : null,
    free_shipping: !!o.free_shipping,
    min_order_value: o.min_order_value != null ? Number(o.min_order_value) : null,
    customer_type: o.customer_type || 'ANY',
    sales_channel: o.sales_channel || 'ECOMMERCE',
    max_uses: o.max_uses != null ? Number(o.max_uses) : null,
    max_uses_per_customer: o.max_uses_per_customer != null ? Number(o.max_uses_per_customer) : null,
    start_date: o.start_date ? String(o.start_date).slice(0, 10) : '',
    end_date: o.end_date ? String(o.end_date).slice(0, 10) : '',
    is_active: o.is_active !== false
  })
  error.value = ''
  showForm.value = true
}

function cancelForm() {
  showForm.value = false
  resetForm()
}

function payload() {
  return {
    code: form.code.trim(),
    description: form.description.trim() || null,
    discount_percentage: form.discount_percentage,
    discount_amount: form.discount_amount,
    free_shipping: form.free_shipping,
    min_order_value: form.min_order_value,
    customer_type: form.customer_type === 'ANY' ? null : form.customer_type,
    sales_channel: form.sales_channel === 'ANY' ? null : form.sales_channel,
    max_uses: form.max_uses,
    max_uses_per_customer: form.max_uses_per_customer,
    start_date: form.start_date || null,
    end_date: form.end_date || null,
    is_active: form.is_active
  }
}

async function submit() {
  error.value = ''
  if (!form.code.trim()) {
    error.value = 'Code is required.'
    return
  }
  loading.value = true
  try {
    const body = payload()
    if (editingId.value) {
      await api(`/offers/${editingId.value}`, { method: 'PATCH', body })
    } else {
      await api('/offers', { method: 'POST', body })
    }
    cancelForm()
    await refresh()
  } catch (e: unknown) {
    error.value = (e as { data?: { message?: string } })?.data?.message || 'Failed'
  } finally {
    loading.value = false
  }
}

async function toggleActive(o: OfferRow) {
  error.value = ''
  try {
    await api(`/offers/${o.id}`, {
      method: 'PATCH',
      body: {
        code: o.code,
        description: o.description,
        discount_percentage: o.discount_percentage,
        discount_amount: o.discount_amount,
        free_shipping: o.free_shipping,
        min_order_value: o.min_order_value,
        customer_type: o.customer_type,
        sales_channel: o.sales_channel,
        item_id: o.item_id,
        max_uses: o.max_uses,
        max_uses_per_customer: o.max_uses_per_customer,
        start_date: o.start_date,
        end_date: o.end_date,
        is_active: !o.is_active
      }
    })
    await refresh()
  } catch (e: unknown) {
    error.value = (e as { data?: { message?: string } })?.data?.message || 'Could not update status'
  }
}

async function removeOffer(o: OfferRow) {
  if (!confirm(`Delete offer ${o.code}? This cannot be undone. Prefer Disable if it was used on past orders.`)) {
    return
  }
  deletingId.value = o.id
  error.value = ''
  try {
    await api(`/offers/${o.id}`, { method: 'DELETE' })
    if (editingId.value === o.id) cancelForm()
    await refresh()
  } catch (e: unknown) {
    error.value = (e as { data?: { message?: string } })?.data?.message || 'Could not delete offer'
  } finally {
    deletingId.value = null
  }
}
</script>

<template>
  <AdminPage
    title="Offers"
    description="Discounts and coupons — create, edit, disable, or delete."
  >
    <template #actions>
      <UButton
        v-if="canWrite"
        @click="showForm && !editingId ? cancelForm() : openCreate()"
      >
        {{ showForm && !editingId ? 'Cancel' : 'New offer' }}
      </UButton>
    </template>

    <form
      v-if="showForm && canWrite"
      class="mb-8 max-w-lg space-y-3 border-b border-gold-300/60 pb-8"
      @submit.prevent="submit"
    >
      <p class="font-display text-xl text-ink">
        {{ formTitle }}
      </p>
      <UFormField label="Code">
        <UInput
          v-model="form.code"
          required
          class="w-full"
          :disabled="!!editingId"
        />
      </UFormField>
      <UFormField label="Description">
        <UInput
          v-model="form.description"
          class="w-full"
        />
      </UFormField>
      <div class="grid grid-cols-2 gap-2">
        <UFormField label="% off">
          <UInput
            v-model.number="form.discount_percentage"
            type="number"
            step="0.01"
            class="w-full"
          />
        </UFormField>
        <UFormField label="₹ off">
          <UInput
            v-model.number="form.discount_amount"
            type="number"
            step="0.01"
            class="w-full"
          />
        </UFormField>
      </div>
      <UFormField label="Min order value">
        <UInput
          v-model.number="form.min_order_value"
          type="number"
          step="0.01"
          class="w-full"
        />
      </UFormField>
      <UFormField label="Party type">
        <USelect
          v-model="form.customer_type"
          :items="partyItems"
          class="w-full"
        />
      </UFormField>
      <UFormField label="Sales channel">
        <USelect
          v-model="form.sales_channel"
          :items="channelItems"
          class="w-full"
        />
      </UFormField>
      <div class="grid grid-cols-2 gap-2">
        <UFormField label="Max uses">
          <UInput
            v-model.number="form.max_uses"
            type="number"
            class="w-full"
          />
        </UFormField>
        <UFormField label="Max uses / customer">
          <UInput
            v-model.number="form.max_uses_per_customer"
            type="number"
            class="w-full"
          />
        </UFormField>
      </div>
      <div class="grid grid-cols-2 gap-2">
        <UFormField label="Start date">
          <UInput
            v-model="form.start_date"
            type="date"
            class="w-full"
          />
        </UFormField>
        <UFormField label="End date">
          <UInput
            v-model="form.end_date"
            type="date"
            class="w-full"
          />
        </UFormField>
      </div>
      <label class="flex items-center gap-2 text-sm text-ink">
        <input
          v-model="form.free_shipping"
          type="checkbox"
          class="rounded border-gold-300"
        >
        Free shipping
      </label>
      <label class="flex items-center gap-2 text-sm text-ink">
        <input
          v-model="form.is_active"
          type="checkbox"
          class="rounded border-gold-300"
        >
        Active
      </label>
      <p
        v-if="error"
        class="text-sm text-red-700"
      >
        {{ error }}
      </p>
      <div class="flex flex-wrap gap-2">
        <UButton
          type="submit"
          :loading="loading"
        >
          {{ editingId ? 'Save changes' : 'Create' }}
        </UButton>
        <UButton
          type="button"
          color="neutral"
          variant="ghost"
          @click="cancelForm"
        >
          Cancel
        </UButton>
      </div>
    </form>

    <p
      v-else-if="error"
      class="mb-4 text-sm text-red-700"
    >
      {{ error }}
    </p>

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
        class="flex flex-wrap items-center justify-between gap-2 py-3"
      >
        <div>
          <p class="font-medium">
            {{ r.code }}
            <span
              class="ml-2 text-xs uppercase"
              :class="r.is_active ? 'text-green-800' : 'text-ink-muted'"
            >{{ r.is_active ? 'active' : 'off' }}</span>
          </p>
          <p class="mt-1 text-sm text-ink-muted">
            <template v-if="r.discount_percentage">{{ r.discount_percentage }}% · </template>
            <template v-if="r.discount_amount">₹{{ r.discount_amount }} · </template>
            <template v-if="r.free_shipping">free ship · </template>
            {{ r.customer_type || 'any' }} · {{ r.sales_channel || 'any' }}
          </p>
          <p
            v-if="r.description"
            class="mt-0.5 text-sm text-ink-muted"
          >
            {{ r.description }}
          </p>
        </div>
        <div
          v-if="canWrite"
          class="flex flex-wrap gap-2"
        >
          <UButton
            size="sm"
            variant="outline"
            @click="openEdit(r)"
          >
            Edit
          </UButton>
          <UButton
            size="sm"
            variant="outline"
            @click="toggleActive(r)"
          >
            {{ r.is_active ? 'Disable' : 'Enable' }}
          </UButton>
          <UButton
            size="sm"
            color="error"
            variant="ghost"
            :loading="deletingId === r.id"
            @click="removeOffer(r)"
          >
            Delete
          </UButton>
        </div>
      </li>
      <li
        v-if="!rows.length && status !== 'pending'"
        class="py-4 text-ink-muted"
      >
        No offers.
      </li>
    </ul>
  </AdminPage>
</template>
