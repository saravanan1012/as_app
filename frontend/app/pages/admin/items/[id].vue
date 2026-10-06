<script setup lang="ts">
definePageMeta({ layout: 'admin', middleware: ['admin'] })

const route = useRoute()
const auth = useAuthStore()
const { api } = useApi()
const id = computed(() => Number(route.params.id))

const { data, refresh } = await useAdminAsyncData(() => `item-${id.value}`, () =>
  api<Record<string, any>>(`/items/${id.value}`)
)
const item = computed(() => data.value?.data)

const form = reactive({
  name: '',
  sale_price: 0,
  cost_price: 0,
  is_online_sale: false,
  is_sellable: true,
  status: 'ACTIVE',
  description: ''
})
const error = ref('')
const saving = ref(false)
const priceSaving = ref(false)

type PriceRow = { party_type: string, mode: string, value: number }
const priceRows = reactive<PriceRow[]>([
  { party_type: 'DISTRIBUTOR', mode: 'PERCENT_OFF', value: 0 },
  { party_type: 'DEALER', mode: 'PERCENT_OFF', value: 0 },
  { party_type: 'RETAILER', mode: 'PERCENT_OFF', value: 0 }
])

const { data: rulesRes, refresh: refreshRules } = await useAdminAsyncData(
  () => `price-rules-${id.value}`,
  () => api<{ data: Array<Record<string, any>> }>(`/party-price-rules?item_id=${id.value}`)
)

watch(item, (i) => {
  if (!i) return
  form.name = i.name
  form.sale_price = Number(i.sale_price)
  form.cost_price = Number(i.cost_price)
  form.is_online_sale = !!i.is_online_sale
  form.is_sellable = !!i.is_sellable
  form.status = i.status
  form.description = i.description || ''
}, { immediate: true })

watch(rulesRes, (r) => {
  const rows = r?.data?.data || []
  for (const pr of priceRows) {
    const found = rows.find((x: any) => x.party_type === pr.party_type)
    if (found) {
      pr.mode = found.mode
      pr.value = Number(found.value)
    }
  }
}, { immediate: true })

async function save() {
  error.value = ''
  saving.value = true
  try {
    await api(`/items/${id.value}`, { method: 'PATCH', body: { ...form } })
    await refresh()
  } catch (e: unknown) {
    error.value = (e as { data?: { message?: string } })?.data?.message || 'Failed'
  } finally {
    saving.value = false
  }
}

async function savePrices() {
  priceSaving.value = true
  error.value = ''
  try {
    await api('/party-price-rules/bulk', {
      method: 'PUT',
      body: {
        item_id: id.value,
        rules: priceRows.map(r => ({
          item_id: id.value,
          party_type: r.party_type,
          mode: r.mode,
          value: r.value,
          status: 'ACTIVE'
        }))
      }
    })
    await refreshRules()
  } catch (e: unknown) {
    error.value = (e as { data?: { message?: string } })?.data?.message || 'Price save failed'
  } finally {
    priceSaving.value = false
  }
}
</script>

<template>
  <AdminPage
    v-if="item"
    :title="item.name"
    :description="item.code"
  >
    <form
      v-if="auth.hasPermission('catalog.items.write')"
      class="max-w-lg space-y-4"
      @submit.prevent="save"
    >
      <UFormField label="Name">
        <UInput
          v-model="form.name"
          class="w-full"
          required
        />
      </UFormField>
      <UFormField label="Description">
        <UTextarea
          v-model="form.description"
          class="w-full"
        />
      </UFormField>
      <div class="grid grid-cols-2 gap-3">
        <UFormField label="Sale price">
          <UInput
            v-model.number="form.sale_price"
            type="number"
            step="0.01"
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
      <UFormField label="Status">
        <USelect
          v-model="form.status"
          :items="[
            { label: 'Active', value: 'ACTIVE' },
            { label: 'Inactive', value: 'INACTIVE' }
          ]"
          class="w-full"
        />
      </UFormField>
      <div class="flex flex-wrap gap-4 text-sm">
        <label class="flex items-center gap-2">
          <input
            v-model="form.is_sellable"
            type="checkbox"
          >
          Sellable
        </label>
        <label class="flex items-center gap-2">
          <input
            v-model="form.is_online_sale"
            type="checkbox"
          >
          Online (Store)
        </label>
      </div>
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
        Save
      </UButton>
    </form>

    <section
      v-if="auth.hasPermission('catalog.items.write')"
      class="mt-10 max-w-xl space-y-3"
    >
      <h2 class="font-display text-xl">
        Trade prices
      </h2>
      <p class="text-sm text-ink-muted">
        Percentage off MSRP, fixed off, or fixed price per party type.
      </p>
      <div
        v-for="row in priceRows"
        :key="row.party_type"
        class="grid grid-cols-[7rem_1fr_6rem] items-end gap-2"
      >
        <p class="pb-2 text-sm font-medium">
          {{ row.party_type }}
        </p>
        <USelect
          v-model="row.mode"
          :items="[
            { label: '% off MSRP', value: 'PERCENT_OFF' },
            { label: 'Fixed off', value: 'FIXED_OFF' },
            { label: 'Fixed price', value: 'FIXED_PRICE' }
          ]"
          class="w-full"
        />
        <UInput
          v-model.number="row.value"
          type="number"
          step="0.01"
          class="w-full"
        />
      </div>
      <UButton
        :loading="priceSaving"
        variant="outline"
        @click="savePrices"
      >
        Save trade prices
      </UButton>
    </section>

    <dl
      v-else
      class="grid gap-3 text-sm sm:grid-cols-2"
    >
      <div>
        <dt class="text-ink-muted">
          Sale
        </dt>
        <dd>₹{{ Number(item.sale_price).toFixed(2) }}</dd>
      </div>
      <div>
        <dt class="text-ink-muted">
          Status
        </dt>
        <dd>{{ item.status }}</dd>
      </div>
      <div>
        <dt class="text-ink-muted">
          Online
        </dt>
        <dd>{{ item.is_online_sale ? 'Yes' : 'No' }}</dd>
      </div>
    </dl>
  </AdminPage>
</template>
