<script setup lang="ts">
definePageMeta({ layout: 'admin', middleware: ['admin'] })

const { api } = useApi()
const error = ref('')
const saving = ref(false)
const catSaving = ref(false)

const taxForm = reactive({
  gst_enabled: true,
  gstin: '',
  state_code: 'TN'
})

const newCat = reactive({
  code: '',
  name: '',
  gst_rate: 12,
  hsn_sac: ''
})

const { data: taxRes, refresh: refreshTax } = await useAdminAsyncData('tax-settings', () =>
  api<Record<string, any>>('/vendor-settings/tax')
)

const { data: catsRes, refresh: refreshCats } = await useAdminAsyncData('tax-categories', () =>
  api<Array<Record<string, any>>>('/tax-categories')
)

const categories = computed(() => {
  const raw = catsRes.value?.data
  return Array.isArray(raw) ? raw : []
})

watch(taxRes, (d) => {
  const t = d?.data
  if (!t) return
  taxForm.gst_enabled = t.gst_enabled !== false
  taxForm.gstin = t.gstin || ''
  taxForm.state_code = t.state_code || 'TN'
}, { immediate: true })

async function saveTax() {
  error.value = ''
  saving.value = true
  try {
    await api('/vendor-settings/tax', {
      method: 'PATCH',
      body: {
        gst_enabled: taxForm.gst_enabled,
        gstin: taxForm.gstin.trim() || null,
        state_code: taxForm.state_code.trim().toUpperCase()
      }
    })
    await refreshTax()
  } catch (e: unknown) {
    error.value = (e as { data?: { message?: string } })?.data?.message || 'Failed'
  } finally {
    saving.value = false
  }
}

async function addCategory() {
  error.value = ''
  if (!newCat.code.trim() || !newCat.name.trim()) {
    error.value = 'Code and name are required'
    return
  }
  catSaving.value = true
  try {
    await api('/tax-categories', {
      method: 'POST',
      body: {
        code: newCat.code.trim().toUpperCase(),
        name: newCat.name.trim(),
        gst_rate: Number(newCat.gst_rate) || 0,
        hsn_sac: newCat.hsn_sac.trim() || null
      }
    })
    newCat.code = ''
    newCat.name = ''
    newCat.gst_rate = 12
    newCat.hsn_sac = ''
    await refreshCats()
  } catch (e: unknown) {
    error.value = (e as { data?: { message?: string } })?.data?.message || 'Create failed'
  } finally {
    catSaving.value = false
  }
}

async function saveCategory(c: Record<string, any>) {
  error.value = ''
  try {
    await api(`/tax-categories/${c.id}`, {
      method: 'PATCH',
      body: {
        name: c.name,
        gst_rate: Number(c.gst_rate) || 0,
        hsn_sac: c.hsn_sac || null
      }
    })
    await refreshCats()
  } catch (e: unknown) {
    error.value = (e as { data?: { message?: string } })?.data?.message || 'Update failed'
  }
}
</script>

<template>
  <AdminPage
    title="GST / Tax"
    description="Enable Online Store GST breakdown · tax categories by rate · vendor state for CGST/SGST vs IGST"
  >
    <div class="max-w-2xl space-y-10">
      <section class="space-y-4 rounded-lg border border-gold-300/50 p-4">
        <h2 class="font-display text-xl text-ink">
          Store GST settings
        </h2>
        <p class="text-sm text-ink-muted">
          When enabled, checkout shows taxable value and CGST+SGST (same state) or IGST (different state).
          Item prices that include GST are not increased again — GST is a breakdown.
        </p>
        <label class="flex items-center gap-2 text-sm text-ink">
          <input
            v-model="taxForm.gst_enabled"
            type="checkbox"
          >
          Show GST on Online Store checkout
        </label>
        <div class="grid grid-cols-2 gap-3">
          <UFormField label="GSTIN">
            <UInput
              v-model="taxForm.gstin"
              class="w-full"
              placeholder="Optional"
            />
          </UFormField>
          <UFormField label="Vendor state code">
            <UInput
              v-model="taxForm.state_code"
              class="w-full"
              maxlength="2"
              placeholder="TN"
            />
          </UFormField>
        </div>
        <UButton
          :loading="saving"
          @click="saveTax"
        >
          Save GST settings
        </UButton>
      </section>

      <section class="space-y-4 rounded-lg border border-gold-300/50 p-4">
        <h2 class="font-display text-xl text-ink">
          Tax categories
        </h2>
        <p class="text-sm text-ink-muted">
          Different products can use different GST %. Assign a category on each item.
        </p>

        <ul class="space-y-3">
          <li
            v-for="c in categories"
            :key="c.id"
            class="grid grid-cols-1 gap-2 border-b border-gold-300/30 pb-3 sm:grid-cols-[1fr_1fr_5rem_6rem_auto] sm:items-end"
          >
            <UFormField :label="`Code`">
              <UInput
                :model-value="c.code"
                disabled
                class="w-full"
              />
            </UFormField>
            <UFormField label="Name">
              <UInput
                v-model="c.name"
                class="w-full"
              />
            </UFormField>
            <UFormField label="Rate %">
              <UInput
                v-model.number="c.gst_rate"
                type="number"
                step="0.01"
                class="w-full"
              />
            </UFormField>
            <UFormField label="HSN">
              <UInput
                v-model="c.hsn_sac"
                class="w-full"
              />
            </UFormField>
            <UButton
              size="sm"
              variant="outline"
              @click="saveCategory(c)"
            >
              Save
            </UButton>
          </li>
        </ul>

        <div class="border-t border-gold-300/40 pt-4">
          <h3 class="text-sm font-medium text-ink">
            Add category
          </h3>
          <div class="mt-3 grid grid-cols-1 gap-2 sm:grid-cols-2">
            <UFormField label="Code">
              <UInput
                v-model="newCat.code"
                class="w-full"
                placeholder="GST12"
              />
            </UFormField>
            <UFormField label="Name">
              <UInput
                v-model="newCat.name"
                class="w-full"
                placeholder="GST 12%"
              />
            </UFormField>
            <UFormField label="Rate %">
              <UInput
                v-model.number="newCat.gst_rate"
                type="number"
                step="0.01"
                class="w-full"
              />
            </UFormField>
            <UFormField label="HSN">
              <UInput
                v-model="newCat.hsn_sac"
                class="w-full"
              />
            </UFormField>
          </div>
          <UButton
            class="mt-3"
            :loading="catSaving"
            @click="addCategory"
          >
            Add tax category
          </UButton>
        </div>
      </section>

      <p
        v-if="error"
        class="text-sm text-red-700"
      >
        {{ error }}
      </p>
    </div>
  </AdminPage>
</template>
