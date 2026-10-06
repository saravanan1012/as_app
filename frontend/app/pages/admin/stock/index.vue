<script setup lang="ts">
definePageMeta({ layout: 'admin', middleware: ['admin'] })

const auth = useAuthStore()
const { api } = useApi()
const tab = ref<'balances' | 'movements' | 'adjust'>('balances')

const { data: stockRes, refresh: refreshStock, status } = await useAdminAsyncData('admin-stock', () =>
  api<Array<Record<string, any>>>('/stock')
)
const { data: movRes, refresh: refreshMov } = await useAdminAsyncData('admin-movements', () =>
  api<{ data: Array<Record<string, any>> }>('/stock-movements?page_size=50')
)
const { data: itemsRes } = await useAdminAsyncData('adj-items', () =>
  api<{ data: Array<{ id: number, name: string }> }>('/items?page_size=200')
)
const { data: locsRes } = await useAdminAsyncData('adj-locs', () =>
  api<Array<{ id: number, name: string }>>('/locations')
)

const balances = computed(() => stockRes.value?.data || [])
const movements = computed(() => movRes.value?.data?.data || [])
const items = computed(() => itemsRes.value?.data?.data || [])
const locs = computed(() => locsRes.value?.data || [])
const itemOptions = computed(() => items.value.map(i => ({ label: i.name, value: i.id })))
const locOptions = computed(() => locs.value.map(l => ({ label: l.name, value: l.id })))

const adj = reactive({
  code: `ADJ-${Date.now()}`,
  adjustment_date: new Date().toISOString().slice(0, 10),
  notes: '',
  item_id: undefined as number | undefined,
  location_id: undefined as number | undefined,
  qty_delta: 0
})
const adjError = ref('')
const adjLoading = ref(false)

watch(locs, (l) => {
  if (adj.location_id == null && l[0]) adj.location_id = l[0].id
}, { immediate: true })

async function submitAdj() {
  adjError.value = ''
  adjLoading.value = true
  try {
    await api('/stock-adjustments', {
      method: 'POST',
      body: {
        code: adj.code,
        adjustment_date: adj.adjustment_date,
        reason: 'ADJUSTMENT',
        notes: adj.notes || null,
        items: [{
          item_id: adj.item_id,
          location_id: adj.location_id,
          qty_delta: adj.qty_delta
        }]
      }
    })
    adj.code = `ADJ-${Date.now()}`
    adj.qty_delta = 0
    tab.value = 'balances'
    await Promise.all([refreshStock(), refreshMov()])
  } catch (e: unknown) {
    adjError.value = (e as { data?: { message?: string } })?.data?.message || 'Failed'
  } finally {
    adjLoading.value = false
  }
}
</script>

<template>
  <AdminPage
    title="Stock"
    description="Balances, ledger, and adjustments"
  >
    <div class="mb-6 flex flex-wrap gap-2">
      <UButton
        :variant="tab === 'balances' ? 'solid' : 'outline'"
        @click="tab = 'balances'"
      >
        Balances
      </UButton>
      <UButton
        :variant="tab === 'movements' ? 'solid' : 'outline'"
        @click="tab = 'movements'"
      >
        Movements
      </UButton>
      <UButton
        v-if="auth.hasPermission('stock.write')"
        :variant="tab === 'adjust' ? 'solid' : 'outline'"
        @click="tab = 'adjust'"
      >
        Adjust
      </UButton>
    </div>

    <div v-if="tab === 'balances'">
      <p
        v-if="status === 'pending'"
        class="text-ink-muted"
      >
        Loading…
      </p>
      <ul class="divide-y divide-gold-300/60 border-y border-gold-300/60">
        <li
          v-for="r in balances"
          :key="r.id"
          class="flex flex-wrap justify-between gap-2 py-3 text-sm"
        >
          <span>Item #{{ r.item_id }} · Loc #{{ r.location_id }}</span>
          <span class="tabular-nums">
            on hand {{ r.quantity_on_hand }} · avail {{ r.quantity_available }}
          </span>
        </li>
        <li
          v-if="!balances.length && status !== 'pending'"
          class="py-4 text-ink-muted"
        >
          No stock rows.
        </li>
      </ul>
    </div>

    <div v-else-if="tab === 'movements'">
      <ul class="divide-y divide-gold-300/60 border-y border-gold-300/60">
        <li
          v-for="m in movements"
          :key="m.id"
          class="py-3 text-sm"
        >
          <div class="flex justify-between gap-2">
            <span>{{ m.reason }} · item #{{ m.item_id }}</span>
            <span
              class="tabular-nums"
              :class="m.qty_delta >= 0 ? 'text-green-800' : 'text-red-700'"
            >
              {{ m.qty_delta > 0 ? '+' : '' }}{{ m.qty_delta }}
            </span>
          </div>
          <p class="mt-1 text-ink-muted">
            after {{ m.qty_after }} · {{ m.reference_type || '—' }} #{{ m.reference_id || '—' }}
          </p>
        </li>
        <li
          v-if="!movements.length"
          class="py-4 text-ink-muted"
        >
          No movements.
        </li>
      </ul>
    </div>

    <form
      v-else
      class="max-w-lg space-y-4"
      @submit.prevent="submitAdj"
    >
      <UFormField label="Code">
        <UInput
          v-model="adj.code"
          required
          class="w-full"
        />
      </UFormField>
      <UFormField label="Date">
        <UInput
          v-model="adj.adjustment_date"
          type="date"
          class="w-full"
        />
      </UFormField>
      <UFormField label="Item">
        <USelect
          v-model="adj.item_id"
          :items="itemOptions"
          value-key="value"
          class="w-full"
          placeholder="Select item"
        />
      </UFormField>
      <UFormField label="Location">
        <USelect
          v-model="adj.location_id"
          :items="locOptions"
          value-key="value"
          class="w-full"
          placeholder="Select location"
        />
      </UFormField>
      <UFormField label="Qty delta (+/−)">
        <UInput
          v-model.number="adj.qty_delta"
          type="number"
          required
          class="w-full"
        />
      </UFormField>
      <UFormField label="Notes">
        <UInput
          v-model="adj.notes"
          class="w-full"
        />
      </UFormField>
      <p
        v-if="adjError"
        class="text-sm text-red-700"
      >
        {{ adjError }}
      </p>
      <UButton
        type="submit"
        :loading="adjLoading"
      >
        Post adjustment
      </UButton>
    </form>
  </AdminPage>
</template>
