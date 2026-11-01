<script setup lang="ts">
definePageMeta({ layout: 'admin', middleware: ['admin'] })

const { api } = useApi()
const error = ref('')
const saving = ref(false)

const form = reactive({
  ecommerce: {
    enabled: true,
    flat_rate: 80,
    interstate_flat_rate: 160,
    free_over_enabled: true,
    free_over: 500 as number | null,
    eta_same_min: 2,
    eta_same_max: 4,
    eta_other_min: 5,
    eta_other_max: 7
  },
  b2b: {
    qty_tiers: [
      { max_qty: 2 as number | null, charge: 80 },
      { max_qty: 9 as number | null, charge: 40 },
      { max_qty: null as number | null, charge: 0 }
    ]
  },
  couriers: ['AKR_PARCEL', 'MARUTHI_PARCEL'] as string[]
})

const { data, refresh } = await useAdminAsyncData('shipping-settings', () =>
  api<Record<string, any>>('/vendor-settings/shipping')
)

watch(data, (d) => {
  const s = d?.data
  if (!s) return
  const eco = s.ecommerce || {}
  form.ecommerce.enabled = eco.enabled !== false
  form.ecommerce.flat_rate = Number(eco.flat_rate ?? 0)
  form.ecommerce.interstate_flat_rate = Number(
    eco.interstate_flat_rate ?? Number(eco.flat_rate ?? 0) * 2
  )
  form.ecommerce.free_over_enabled = !!eco.free_over_enabled
  form.ecommerce.free_over = eco.free_over != null ? Number(eco.free_over) : null
  form.ecommerce.eta_same_min = Number(eco.eta_same_min ?? 2)
  form.ecommerce.eta_same_max = Number(eco.eta_same_max ?? 4)
  form.ecommerce.eta_other_min = Number(eco.eta_other_min ?? 5)
  form.ecommerce.eta_other_max = Number(eco.eta_other_max ?? 7)
  const tiers = s.b2b?.qty_tiers || s.qty_tiers
  if (Array.isArray(tiers) && tiers.length) {
    form.b2b.qty_tiers = tiers.map((t: any) => ({
      max_qty: t.max_qty == null ? null : Number(t.max_qty),
      charge: Number(t.charge || 0)
    }))
  }
  if (Array.isArray(s.couriers) && s.couriers.length) {
    form.couriers = [...s.couriers]
  }
}, { immediate: true })

function addTier() {
  form.b2b.qty_tiers.push({ max_qty: null, charge: 0 })
}

function removeTier(i: number) {
  form.b2b.qty_tiers.splice(i, 1)
}

async function save() {
  error.value = ''
  saving.value = true
  try {
    await api('/vendor-settings/shipping', {
      method: 'PATCH',
      body: {
        ecommerce: {
          enabled: form.ecommerce.enabled,
          flat_rate: form.ecommerce.flat_rate,
          interstate_flat_rate: form.ecommerce.interstate_flat_rate,
          free_over_enabled: form.ecommerce.free_over_enabled,
          free_over: form.ecommerce.free_over_enabled ? form.ecommerce.free_over : null,
          eta_same_min: form.ecommerce.eta_same_min,
          eta_same_max: form.ecommerce.eta_same_max,
          eta_other_min: form.ecommerce.eta_other_min,
          eta_other_max: form.ecommerce.eta_other_max
        },
        b2b: { qty_tiers: form.b2b.qty_tiers },
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
    description="Online Store uses amount-based delivery · B2B uses qty tiers (bags/units)"
  >
    <form
      class="max-w-xl space-y-10"
      @submit.prevent="save"
    >
      <section class="space-y-4 rounded-lg border border-gold-300/50 p-4">
        <div>
          <h2 class="font-display text-xl text-ink">
            Online Store (direct customers)
          </h2>
          <p class="mt-1 text-sm text-ink-muted">
            Same-state uses vendor tax state (e.g. TN). Other states use the interstate rate.
            Free delivery above a threshold applies to both zones.
          </p>
        </div>

        <label class="flex items-center gap-2 text-sm text-ink">
          <input
            v-model="form.ecommerce.enabled"
            type="checkbox"
          >
          Delivery charges enabled for Online Store
        </label>

        <UFormField label="Same-state delivery ₹">
          <UInput
            v-model.number="form.ecommerce.flat_rate"
            type="number"
            step="0.01"
            class="w-full"
            :disabled="!form.ecommerce.enabled"
          />
        </UFormField>

        <UFormField label="Interstate delivery ₹">
          <UInput
            v-model.number="form.ecommerce.interstate_flat_rate"
            type="number"
            step="0.01"
            class="w-full"
            :disabled="!form.ecommerce.enabled"
          />
        </UFormField>

        <label class="flex items-center gap-2 text-sm text-ink">
          <input
            v-model="form.ecommerce.free_over_enabled"
            type="checkbox"
            :disabled="!form.ecommerce.enabled"
          >
          Free delivery above amount
        </label>

        <UFormField
          v-if="form.ecommerce.free_over_enabled"
          label="Free over ₹"
        >
          <UInput
            v-model.number="form.ecommerce.free_over"
            type="number"
            step="0.01"
            class="w-full"
            :disabled="!form.ecommerce.enabled"
            placeholder="e.g. 500"
          />
        </UFormField>

        <div class="grid grid-cols-2 gap-3">
          <UFormField label="Same-state ETA min (days)">
            <UInput
              v-model.number="form.ecommerce.eta_same_min"
              type="number"
              min="0"
              class="w-full"
              :disabled="!form.ecommerce.enabled"
            />
          </UFormField>
          <UFormField label="Same-state ETA max (days)">
            <UInput
              v-model.number="form.ecommerce.eta_same_max"
              type="number"
              min="0"
              class="w-full"
              :disabled="!form.ecommerce.enabled"
            />
          </UFormField>
          <UFormField label="Other-state ETA min (days)">
            <UInput
              v-model.number="form.ecommerce.eta_other_min"
              type="number"
              min="0"
              class="w-full"
              :disabled="!form.ecommerce.enabled"
            />
          </UFormField>
          <UFormField label="Other-state ETA max (days)">
            <UInput
              v-model.number="form.ecommerce.eta_other_max"
              type="number"
              min="0"
              class="w-full"
              :disabled="!form.ecommerce.enabled"
            />
          </UFormField>
        </div>
      </section>

      <section class="space-y-4 rounded-lg border border-gold-300/50 p-4">
        <div class="flex items-center justify-between gap-3">
          <div>
            <h2 class="font-display text-xl text-ink">
              B2B (distributor / dealer / retailer)
            </h2>
            <p class="mt-1 text-sm text-ink-muted">
              Qty tiers by total bags/units — mainly napkin trade orders.
            </p>
          </div>
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
          v-for="(tier, i) in form.b2b.qty_tiers"
          :key="i"
          class="grid grid-cols-[1fr_1fr_auto] gap-2"
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
          <div class="flex items-end pb-1">
            <UButton
              type="button"
              size="sm"
              variant="ghost"
              color="neutral"
              :disabled="form.b2b.qty_tiers.length <= 1"
              @click="removeTier(i)"
            >
              Remove
            </UButton>
          </div>
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
