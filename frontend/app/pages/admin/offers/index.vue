<script setup lang="ts">
definePageMeta({ layout: 'admin', middleware: ['admin'] })

const auth = useAuthStore()
const { api } = useApi()
const showNew = ref(false)

const { data, refresh, status } = await useAdminAsyncData('admin-offers', () =>
  api<Array<Record<string, any>>>('/offers')
)
const rows = computed(() => data.value?.data || [])

const form = reactive({
  code: '',
  description: '',
  discount_percentage: null as number | null,
  discount_amount: null as number | null,
  min_order_value: null as number | null,
  customer_type: 'ANY',
  sales_channel: 'ECOMMERCE',
  is_active: true
})
const error = ref('')
const loading = ref(false)

async function submit() {
  error.value = ''
  loading.value = true
  try {
    await api('/offers', {
      method: 'POST',
      body: {
        code: form.code,
        description: form.description || null,
        discount_percentage: form.discount_percentage,
        discount_amount: form.discount_amount,
        min_order_value: form.min_order_value,
        customer_type: form.customer_type === 'ANY' ? null : form.customer_type,
        sales_channel: form.sales_channel,
        is_active: form.is_active
      }
    })
    Object.assign(form, {
      code: '',
      description: '',
      discount_percentage: null,
      discount_amount: null,
      min_order_value: null,
      customer_type: 'ANY',
      sales_channel: 'ECOMMERCE',
      is_active: true
    })
    showNew.value = false
    await refresh()
  } catch (e: unknown) {
    error.value = (e as { data?: { message?: string } })?.data?.message || 'Failed'
  } finally {
    loading.value = false
  }
}

async function toggleActive(o: Record<string, any>) {
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
}
</script>

<template>
  <AdminPage
    title="Offers"
    description="Discounts and coupons"
  >
    <template #actions>
      <UButton
        v-if="auth.hasPermission('offers.write')"
        @click="showNew = !showNew"
      >
        {{ showNew ? 'Cancel' : 'New offer' }}
      </UButton>
    </template>

    <form
      v-if="showNew"
      class="mb-8 max-w-lg space-y-3 border-b border-gold-300/60 pb-8"
      @submit.prevent="submit"
    >
      <UFormField label="Code">
        <UInput
          v-model="form.code"
          required
          class="w-full"
        />
      </UFormField>
      <UFormField label="Description">
        <UInput
          v-model="form.description"
          class="w-full"
        />
      </UFormField>
      <div class="grid grid-cols-2 gap-2">
        <UInput
          v-model.number="form.discount_percentage"
          type="number"
          placeholder="% off"
        />
        <UInput
          v-model.number="form.discount_amount"
          type="number"
          placeholder="₹ off"
        />
      </div>
      <UInput
        v-model.number="form.min_order_value"
        type="number"
        placeholder="Min order value"
        class="w-full"
      />
      <USelect
        v-model="form.customer_type"
        :items="[
          { label: 'Any party', value: 'ANY' },
          { label: 'Distributor', value: 'DISTRIBUTOR' },
          { label: 'Dealer', value: 'DEALER' },
          { label: 'Retailer', value: 'RETAILER' },
          { label: 'Customer', value: 'CUSTOMER' }
        ]"
        class="w-full"
      />
      <p
        v-if="error"
        class="text-sm text-red-700"
      >
        {{ error }}
      </p>
      <UButton
        type="submit"
        :loading="loading"
      >
        Create
      </UButton>
    </form>

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
            {{ r.customer_type || 'any' }} · {{ r.sales_channel }}
          </p>
        </div>
        <UButton
          v-if="auth.hasPermission('offers.write')"
          size="sm"
          variant="outline"
          @click="toggleActive(r)"
        >
          {{ r.is_active ? 'Disable' : 'Enable' }}
        </UButton>
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
