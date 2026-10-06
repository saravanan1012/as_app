<script setup lang="ts">
definePageMeta({ layout: 'admin', middleware: ['admin'] })

const { api } = useApi()
const today = new Date().toISOString().slice(0, 10)
const { data: itemsRes } = await useAdminAsyncData('po-items', () =>
  api<{ data: Array<{ id: number, name: string, cost_price: number }> }>('/items?page_size=200')
)
const { data: locsRes } = await useAdminAsyncData('po-locs', () => api<Array<{ id: number, name: string }>>('/locations'))
const { data: supRes } = await useAdminAsyncData('po-sup', () => api<Array<{ id: number, name: string }>>('/suppliers'))

const items = computed(() => itemsRes.value?.data?.data || [])
const locs = computed(() => locsRes.value?.data || [])
const suppliers = computed(() => supRes.value?.data || [])

const form = reactive({
  order_code: `PO-${Date.now()}`,
  order_date: today,
  supplier_id: null as number | null,
  item_id: null as number | null,
  location_id: null as number | null,
  quantity_ordered: 10,
  cost_price: 0,
  status: 'ORDERED'
})
const error = ref('')
const loading = ref(false)

watch(() => form.item_id, (id) => {
  const it = items.value.find(i => i.id === id)
  if (it) form.cost_price = Number(it.cost_price)
})
watch(locs, (l) => { if (!form.location_id && l[0]) form.location_id = l[0].id }, { immediate: true })
watch(suppliers, (s) => { if (!form.supplier_id && s[0]) form.supplier_id = s[0].id }, { immediate: true })

async function submit() {
  error.value = ''
  loading.value = true
  try {
    const res = await api<{ id: number }>('/purchase-orders', {
      method: 'POST',
      body: {
        order_code: form.order_code,
        order_date: form.order_date,
        supplier_id: form.supplier_id,
        status: form.status,
        items: [{
          item_id: form.item_id,
          location_id: form.location_id,
          quantity_ordered: form.quantity_ordered,
          cost_price: form.cost_price
        }]
      }
    })
    await navigateTo(`/admin/purchase-orders/${res.data.id}`)
  } catch (e: unknown) {
    error.value = (e as { data?: { message?: string } })?.data?.message || 'Failed'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <AdminPage title="New purchase order">
    <form
      class="max-w-lg space-y-4"
      @submit.prevent="submit"
    >
      <UFormField label="Code">
        <UInput
          v-model="form.order_code"
          class="w-full"
          required
        />
      </UFormField>
      <UFormField label="Supplier">
        <USelect
          v-model="form.supplier_id"
          :items="suppliers.map(s => ({ label: s.name, value: s.id }))"
          class="w-full"
        />
      </UFormField>
      <UFormField label="Item">
        <USelect
          v-model="form.item_id"
          :items="items.map(i => ({ label: i.name, value: i.id }))"
          class="w-full"
        />
      </UFormField>
      <div class="grid grid-cols-2 gap-3">
        <UFormField label="Qty">
          <UInput
            v-model.number="form.quantity_ordered"
            type="number"
            min="1"
            class="w-full"
          />
        </UFormField>
        <UFormField label="Cost">
          <UInput
            v-model.number="form.cost_price"
            type="number"
            step="0.01"
            class="w-full"
          />
        </UFormField>
      </div>
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
        Create PO
      </UButton>
    </form>
  </AdminPage>
</template>
