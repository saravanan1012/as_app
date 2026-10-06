<script setup lang="ts">
definePageMeta({ layout: 'admin', middleware: ['admin'] })

const { api } = useApi()
const error = ref('')
const saving = ref(false)

const form = reactive({
  flat_rate: 0,
  free_over: null as number | null,
  qty_tiers: [
    { max_qty: 2 as number | null, charge: 80 },
    { max_qty: 9 as number | null, charge: 40 },
    { max_qty: null as number | null, charge: 0 }
  ],
  couriers: ['AKR_PARCEL', 'MARUTHI_PARCEL'] as string[]
})

const { data, refresh } = await useAdminAsyncData('shipping-settings', () =>
  api<Record<string, any>>('/vendor-settings/shipping')
)

watch(data, (d) => {
  const s = d?.data
  if (!s) return
  form.flat_rate = Number(s.flat_rate || 0)
  form.free_over = s.free_over != null ? Number(s.free_over) : null
  if (Array.isArray(s.qty_tiers) && s.qty_tiers.length) {
    form.qty_tiers = s.qty_tiers.map((t: any) => ({
      max_qty: t.max_qty == null ? null : Number(t.max_qty),
      charge: Number(t.charge || 0)
    }))
  }
  if (Array.isArray(s.couriers) && s.couriers.length) {
    form.couriers = [...s.couriers]
  }
}, { immediate: true })

function addTier() {
  form.qty_tiers.push({ max_qty: null, charge: 0 })
}

async function save() {
  error.value = ''
  saving.value = true
  try {
    await api('/vendor-settings/shipping', {
      method: 'PATCH',
      body: {
        flat_rate: form.flat_rate,
        free_over: form.free_over,
        qty_tiers: form.qty_tiers,
        couriers: form.couriers
      }
    })
    await refresh()
  } catch (e: unknown) {
    error.value = (e as { data?: { message?: string } })?.data?.message || 'Failed'
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <AdminPage
    title="Shipping"
    description="Delivery charge by total bags/units in cart · courier allowlist"
  >
    <form
      class="max-w-xl space-y-6"
      @submit.prevent="save"
    >
      <div class="grid grid-cols-2 gap-3">
        <UFormField label="Flat rate (fallback)">
          <UInput
            v-model.number="form.flat_rate"
            type="number"
            step="0.01"
            class="w-full"
          />
        </UFormField>
        <UFormField label="Free over (fallback)">
          <UInput
            v-model.number="form.free_over"
            type="number"
            step="0.01"
            class="w-full"
            placeholder="Optional"
          />
        </UFormField>
      </div>

      <section class="space-y-3">
        <div class="flex items-center justify-between">
          <h2 class="font-display text-lg">
            Qty tiers
          </h2>
          <UButton
            type="button"
            size="sm"
            variant="outline"
            @click="addTier"
          >
            Add tier
          </UButton>
        </div>
        <p class="text-sm text-ink-muted">
          First matching max qty (ascending) wins. Leave max empty for unlimited (e.g. ≥10 free).
        </p>
        <div
          v-for="(tier, i) in form.qty_tiers"
          :key="i"
          class="grid grid-cols-2 gap-2"
        >
          <UFormField :label="`Max qty #${i + 1}`">
            <UInput
              v-model.number="tier.max_qty"
              type="number"
              class="w-full"
              placeholder="Unlimited"
            />
          </UFormField>
          <UFormField label="Charge ₹">
            <UInput
              v-model.number="tier.charge"
              type="number"
              step="0.01"
              class="w-full"
            />
          </UFormField>
        </div>
      </section>

      <section>
        <h2 class="font-display text-lg">
          Couriers
        </h2>
        <p class="mt-1 text-sm text-ink-muted">
          AKR Parcel · Maruthi Parcel
        </p>
        <p class="mt-2 text-sm">
          {{ form.couriers.join(', ') }}
        </p>
      </section>

      <p
        v-if="error"
        class="text-sm text-red-700"
      >
        {{ error }}
      </p>
      <UButton
        type="submit"
        :loading="saving"
      >
        Save shipping
      </UButton>
    </form>
  </AdminPage>
</template>
