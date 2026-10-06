<script setup lang="ts">
definePageMeta({ layout: 'admin', middleware: ['admin'] })

const { api } = useApi()
const form = reactive({
  code: '',
  name: '',
  description: '',
  sale_price: 0,
  cost_price: 0,
  unit_of_measure: 'PCS',
  category: 'GENERAL',
  is_sellable: true,
  is_online_sale: false,
  sale_price_includes_gst: true,
  status: 'ACTIVE'
})
const error = ref('')
const loading = ref(false)

async function submit() {
  error.value = ''
  loading.value = true
  try {
    const res = await api<{ id: number }>('/items', { method: 'POST', body: { ...form } })
    await navigateTo(`/admin/items/${res.data.id}`)
  } catch (e: unknown) {
    error.value = (e as { data?: { message?: string } })?.data?.message || 'Failed'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <AdminPage
    title="New item"
    description="Add a catalog product"
  >
    <form
      class="max-w-lg space-y-4"
      @submit.prevent="submit"
    >
      <UFormField label="Code">
        <UInput
          v-model="form.code"
          required
          class="w-full"
        />
      </UFormField>
      <UFormField label="Name">
        <UInput
          v-model="form.name"
          required
          class="w-full"
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
        <UFormField label="Cost price">
          <UInput
            v-model.number="form.cost_price"
            type="number"
            step="0.01"
            class="w-full"
          />
        </UFormField>
      </div>
      <UFormField label="Unit">
        <UInput
          v-model="form.unit_of_measure"
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
        <label class="flex items-center gap-2">
          <input
            v-model="form.sale_price_includes_gst"
            type="checkbox"
          >
          Price includes GST
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
        :loading="loading"
      >
        Create
      </UButton>
    </form>
  </AdminPage>
</template>
