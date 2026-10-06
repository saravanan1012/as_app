<script setup lang="ts">
definePageMeta({ layout: 'admin', middleware: ['admin'] })

const auth = useAuthStore()
const { api } = useApi()
const showNew = ref(false)

const { data, refresh, status } = await useAdminAsyncData('admin-tx', () =>
  api<Array<Record<string, any>>>('/transactions')
)
const rows = computed(() => data.value?.data || [])

const form = reactive({
  transaction_date: new Date().toISOString().slice(0, 10),
  amount: 0,
  type: 'PAYMENT',
  direction: 'IN',
  payment_method: 'CASH',
  notes: ''
})
const error = ref('')
const loading = ref(false)

async function submit() {
  error.value = ''
  loading.value = true
  try {
    await api('/transactions', { method: 'POST', body: { ...form } })
    form.amount = 0
    form.notes = ''
    showNew.value = false
    await refresh()
  } catch (e: unknown) {
    error.value = (e as { data?: { message?: string } })?.data?.message || 'Failed'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <AdminPage
    title="Transactions"
    description="Payments and cash movements"
  >
    <template #actions>
      <UButton
        v-if="auth.hasPermission('transactions.write')"
        @click="showNew = !showNew"
      >
        {{ showNew ? 'Cancel' : 'Record' }}
      </UButton>
    </template>

    <form
      v-if="showNew"
      class="mb-8 max-w-lg space-y-3 border-b border-gold-300/60 pb-8"
      @submit.prevent="submit"
    >
      <UFormField label="Date">
        <UInput
          v-model="form.transaction_date"
          type="date"
          class="w-full"
          required
        />
      </UFormField>
      <UFormField label="Amount">
        <UInput
          v-model.number="form.amount"
          type="number"
          step="0.01"
          class="w-full"
          required
        />
      </UFormField>
      <div class="grid grid-cols-2 gap-2">
        <USelect
          v-model="form.direction"
          :items="[
            { label: 'In', value: 'IN' },
            { label: 'Out', value: 'OUT' }
          ]"
        />
        <USelect
          v-model="form.payment_method"
          :items="[
            { label: 'Cash', value: 'CASH' },
            { label: 'UPI', value: 'UPI' },
            { label: 'Bank', value: 'BANK' },
            { label: 'Card', value: 'CARD' }
          ]"
        />
      </div>
      <UInput
        v-model="form.notes"
        placeholder="Notes"
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
        Save
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
        class="flex flex-wrap justify-between gap-2 py-3 text-sm"
      >
        <div>
          <p class="font-medium">
            {{ r.transaction_date }} · {{ r.payment_method || r.type || '—' }}
          </p>
          <p class="mt-1 text-ink-muted">
            {{ r.notes || r.reference_type || '—' }}
          </p>
        </div>
        <span
          class="tabular-nums font-semibold"
          :class="r.direction === 'OUT' ? 'text-red-700' : 'text-green-800'"
        >
          {{ r.direction === 'OUT' ? '−' : '+' }}₹{{ Number(r.amount).toFixed(0) }}
        </span>
      </li>
      <li
        v-if="!rows.length && status !== 'pending'"
        class="py-4 text-ink-muted"
      >
        No transactions.
      </li>
    </ul>
  </AdminPage>
</template>
