<script setup lang="ts">
definePageMeta({ layout: 'admin', middleware: ['admin'] })

const { api } = useApi()
const today = new Date().toISOString().slice(0, 10)

const { data: itemsRes } = await useAdminAsyncData('so-items', () =>
  api<{ data: Array<{ id: number, name: string, sale_price: number }> }>('/items?page_size=200')
)
const { data: locsRes } = await useAdminAsyncData('so-locs', () =>
  api<Array<{ id: number, name: string }>>('/locations')
)
const { data: custRes } = await useAdminAsyncData('so-cust', () =>
  api<{ data: Array<{ id: number, name: string }> }>('/customers?page_size=200')
)

const items = computed(() => itemsRes.value?.data?.data || [])
const locs = computed(() => locsRes.value?.data || [])
const customers = computed(() => custRes.value?.data?.data || [])

const form = reactive({
  order_code: `SO-${Date.now()}`,
  order_date: today,
  customer_id: null as number | null,
  status: 'CONFIRMED',
  item_id: null as number | null,
  location_id: null as number | null,
  quantity: 1,
  unit_price: 0
})
const error = ref('')
const loading = ref(false)

watch(() => form.item_id, (id) => {
  const it = items.value.find(i => i.id === id)
  if (it) form.unit_price = Number(it.sale_price)
})
watch(locs, (l) => {
  if (!form.location_id && l[0]) form.location_id = l[0].id
}, { immediate: true })

async function submit() {
  error.value = ''
  loading.value = true
  try {
    const res = await api<{ id: number }>('/sale-orders', {
      method: 'POST',
      body: {
        order_code: form.order_code,
        order_date: form.order_date,
        customer_id: form.customer_id,
        status: form.status,
        items: [{
          item_id: form.item_id,
          location_id: form.location_id,
          quantity: form.quantity,
          unit_price: form.unit_price
        }]
      }
    })
    await navigateTo(`/admin/sales-orders/${res.data.id}`)
  } catch (e: unknown) {
    error.value = (e as { data?: { message?: string } })?.data?.message || 'Failed'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <AdminPage title="New sale">
    <form
      class="max-w-lg space-y-4"
      @submit.prevent="submit"
    >
      <UFormField label="Order code">
        <UInput
          v-model="form.order_code"
          class="w-full"
          required
        />
      </UFormField>
      <UFormField label="Date">
        <UInput
          v-model="form.order_date"
          type="date"
          class="w-full"
          required
        />
      </UFormField>
      <UFormField label="Customer">
        <USelect
          v-model="form.customer_id"
          :items="customers.map(c => ({ label: c.name, value: c.id }))"
          class="w-full"
          placeholder="Optional"
        />
      </UFormField>
      <UFormField label="Item">
        <USelect
          v-model="form.item_id"
          :items="items.map(i => ({ label: i.name, value: i.id }))"
          class="w-full"
          required
        />
      </UFormField>
      <UFormField label="Location">
        <USelect
          v-model="form.location_id"
          :items="locs.map(l => ({ label: l.name, value: l.id }))"
          class="w-full"
        />
      </UFormField>
      <div class="grid grid-cols-2 gap-3">
        <UFormField label="Qty">
          <UInput
            v-model.number="form.quantity"
            type="number"
            min="1"
            class="w-full"
          />
        </UFormField>
        <UFormField label="Unit price">
          <UInput
            v-model.number="form.unit_price"
            type="number"
            step="0.01"
            class="w-full"
          />
        </UFormField>
      </div>
      <UFormField label="Status">
        <USelect
          v-model="form.status"
          :items="[
            { label: 'Draft', value: 'DRAFT' },
            { label: 'Confirmed', value: 'CONFIRMED' }
          ]"
          class="w-full"
        />
      </UFormField>
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
  </AdminPage>
</template>
