<script setup lang="ts">
definePageMeta({ layout: 'admin', middleware: ['admin'] })

const auth = useAuthStore()
const { api } = useApi()
const showNew = ref(false)

const { data, refresh, status } = await useAdminAsyncData('admin-suppliers', () =>
  api<Array<Record<string, any>>>('/suppliers')
)
const rows = computed(() => data.value?.data || [])

const form = reactive({
  code: '',
  name: '',
  phone: '',
  email: '',
  gstin: '',
  contact_person: ''
})
const error = ref('')
const loading = ref(false)

async function submit() {
  error.value = ''
  loading.value = true
  try {
    await api('/suppliers', { method: 'POST', body: { ...form } })
    Object.assign(form, { code: '', name: '', phone: '', email: '', gstin: '', contact_person: '' })
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
    title="Suppliers"
    description="Purchase vendors"
  >
    <template #actions>
      <UButton
        v-if="auth.hasPermission('suppliers.write')"
        @click="showNew = !showNew"
      >
        {{ showNew ? 'Cancel' : 'New supplier' }}
      </UButton>
    </template>

    <form
      v-if="showNew"
      class="mb-8 max-w-lg space-y-3 border-b border-gold-300/60 pb-8"
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
      <div class="grid grid-cols-2 gap-2">
        <UInput
          v-model="form.phone"
          placeholder="Phone"
        />
        <UInput
          v-model="form.email"
          placeholder="Email"
        />
      </div>
      <UInput
        v-model="form.gstin"
        placeholder="GSTIN"
        class="w-full"
      />
      <UInput
        v-model="form.contact_person"
        placeholder="Contact person"
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
        Create
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
        class="py-3"
      >
        <div class="flex justify-between gap-2">
          <span class="font-medium">{{ r.name }}</span>
          <span class="text-sm text-ink-muted">{{ r.code }}</span>
        </div>
        <p class="mt-1 text-sm text-ink-muted">
          {{ r.phone || '—' }} · {{ r.gstin || 'no GSTIN' }}
        </p>
      </li>
      <li
        v-if="!rows.length && status !== 'pending'"
        class="py-4 text-ink-muted"
      >
        No suppliers.
      </li>
    </ul>
  </AdminPage>
</template>
