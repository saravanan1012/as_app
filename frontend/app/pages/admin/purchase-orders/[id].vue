<script setup lang="ts">
definePageMeta({ layout: 'admin', middleware: ['admin'] })

const route = useRoute()
const { api } = useApi()
const id = computed(() => Number(route.params.id))
const { data, refresh } = await useAdminAsyncData(() => `po-${id.value}`, () =>
  api<Record<string, any>>(`/purchase-orders/${id.value}`)
)
const po = computed(() => data.value?.data)
const qty = ref(1)
const error = ref('')

async function receive(detailId: number) {
  error.value = ''
  try {
    await api(`/purchase-orders/${id.value}/receive`, {
      method: 'POST',
      body: {
        receipt_code: `GRN-${Date.now()}`,
        lines: [{ purchase_order_detail_id: detailId, quantity: qty.value }]
      }
    })
    await refresh()
  } catch (e: unknown) {
    error.value = (e as { data?: { message?: string } })?.data?.message || 'Receive failed'
  }
}
</script>

<template>
  <AdminPage
    v-if="po"
    :title="po.order_code"
    :description="`${po.status} · ₹${Number(po.total_purchase_cost).toFixed(2)}`"
  >
    <p
      v-if="error"
      class="mb-4 text-sm text-red-700"
    >
      {{ error }}
    </p>
    <ul class="divide-y divide-gold-300/60 border-y border-gold-300/60">
      <li
        v-for="line in po.items || []"
        :key="line.id"
        class="space-y-2 py-4"
      >
        <div class="flex justify-between text-sm">
          <span>Item #{{ line.item_id }}</span>
          <span>{{ line.quantity_received }}/{{ line.quantity_ordered }} recv</span>
        </div>
        <div
          v-if="line.quantity_received < line.quantity_ordered"
          class="flex flex-wrap items-end gap-2"
        >
          <UFormField label="Receive qty">
            <UInput
              v-model.number="qty"
              type="number"
              min="1"
              class="w-24"
            />
          </UFormField>
          <UButton @click="receive(line.id)">
            Receive GRN
          </UButton>
        </div>
      </li>
    </ul>
  </AdminPage>
</template>
