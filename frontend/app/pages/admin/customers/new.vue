<script setup lang="ts">
definePageMeta({ layout: 'admin', middleware: ['admin'] })

const { api } = useApi()
const form = reactive({
  name: '',
  party_type: 'CUSTOMER',
  parent_id: null as number | null,
  acquisition_source: 'WALK_IN',
  phone: '',
  email: '',
  street: '',
  city: '',
  state: '',
  zip: ''
})
const error = ref('')
const loading = ref(false)

const parentTypes = computed(() => {
  if (form.party_type === 'DEALER') return ['DISTRIBUTOR']
  if (form.party_type === 'RETAILER') return ['DEALER', 'DISTRIBUTOR']
  if (form.party_type === 'CUSTOMER') return ['RETAILER', 'DEALER', 'DISTRIBUTOR']
  return [] as string[]
})

const { data: parentsRes, refresh: refreshParents } = await useAdminAsyncData(
  'parent-options',
  async () => {
    if (!parentTypes.value.length) return { data: { data: [] as Array<{ id: number, name: string, party_type: string }> } }
    const all: Array<{ id: number, name: string, party_type: string }> = []
    for (const pt of parentTypes.value) {
      const res = await api<{ data: Array<{ id: number, name: string, party_type: string }> }>(
        `/customers?party_type=${pt}&page_size=200`
      )
      all.push(...(res.data?.data || []))
    }
    return { data: { data: all } }
  },
  { watch: [parentTypes] }
)
const parents = computed(() => parentsRes.value?.data?.data || [])

watch(() => form.party_type, () => {
  form.parent_id = null
  refreshParents()
})

async function submit() {
  error.value = ''
  loading.value = true
  try {
    const body: Record<string, unknown> = {
      name: form.name,
      party_type: form.party_type,
      parent_id: form.parent_id,
      acquisition_source: form.acquisition_source,
      phone: form.phone || null,
      email: form.email || null
    }
    if (form.street || form.city) {
      body.address = {
        street: form.street || null,
        city: form.city || null,
        state: form.state || null,
        zip: form.zip || null
      }
    }
    const res = await api<{ id: number }>('/customers', { method: 'POST', body })
    await navigateTo(`/admin/customers/${res.data.id}`)
  } catch (e: unknown) {
    error.value = (e as { data?: { message?: string } })?.data?.message || 'Failed'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <AdminPage
    title="New party"
    description="Hierarchy: Distributor → Dealer → Retailer → Customer"
  >
    <form
      class="max-w-lg space-y-4"
      @submit.prevent="submit"
    >
      <UFormField label="Name">
        <UInput
          v-model="form.name"
          required
          class="w-full"
          size="lg"
        />
      </UFormField>
      <UFormField label="Party type">
        <USelect
          v-model="form.party_type"
          :items="[
            { label: 'Distributor', value: 'DISTRIBUTOR' },
            { label: 'Dealer', value: 'DEALER' },
            { label: 'Retailer', value: 'RETAILER' },
            { label: 'Customer', value: 'CUSTOMER' }
          ]"
          class="w-full"
        />
      </UFormField>
      <UFormField
        v-if="parentTypes.length"
        label="Parent"
      >
        <USelect
          v-model="form.parent_id"
          :items="parents.map(p => ({ label: `${p.name} (${p.party_type})`, value: p.id }))"
          class="w-full"
          placeholder="Select parent (optional)"
        />
      </UFormField>
      <UFormField label="Acquisition">
        <USelect
          v-model="form.acquisition_source"
          :items="[
            { label: 'Walk-in', value: 'WALK_IN' },
            { label: 'Online', value: 'ONLINE' },
            { label: 'FB lead', value: 'FB_LEAD' },
            { label: 'Referral', value: 'REFERRAL' },
            { label: 'Phone', value: 'PHONE' },
            { label: 'Other', value: 'OTHER' }
          ]"
          class="w-full"
        />
      </UFormField>
      <UFormField label="Phone">
        <UInput
          v-model="form.phone"
          class="w-full"
        />
      </UFormField>
      <UFormField label="Email">
        <UInput
          v-model="form.email"
          type="email"
          class="w-full"
        />
      </UFormField>
      <UFormField label="Street">
        <UInput
          v-model="form.street"
          class="w-full"
        />
      </UFormField>
      <div class="grid grid-cols-3 gap-2">
        <UInput
          v-model="form.city"
          placeholder="City"
        />
        <UInput
          v-model="form.state"
          placeholder="State"
        />
        <UInput
          v-model="form.zip"
          placeholder="PIN"
        />
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
        Create
      </UButton>
    </form>
  </AdminPage>
</template>
