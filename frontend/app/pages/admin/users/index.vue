<script setup lang="ts">
definePageMeta({ layout: 'admin', middleware: ['admin'] })

const auth = useAuthStore()
const { api } = useApi()
const showNew = ref(false)

const { data, refresh, status } = await useAdminAsyncData('admin-users', () =>
  api<Array<Record<string, any>>>('/users')
)
const rows = computed(() => data.value?.data || [])

const form = reactive({
  email: '',
  name: '',
  password: '',
  role: 'STAFF',
  phone: ''
})
const error = ref('')
const loading = ref(false)

async function submit() {
  error.value = ''
  loading.value = true
  try {
    await api('/users', { method: 'POST', body: { ...form } })
    Object.assign(form, { email: '', name: '', password: '', role: 'STAFF', phone: '' })
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
    title="Users"
    description="Vendor staff accounts"
  >
    <template #actions>
      <UButton
        v-if="auth.hasPermission('users.write')"
        @click="showNew = !showNew"
      >
        {{ showNew ? 'Cancel' : 'Invite' }}
      </UButton>
    </template>

    <form
      v-if="showNew"
      class="mb-8 max-w-lg space-y-3 border-b border-gold-300/60 pb-8"
      @submit.prevent="submit"
    >
      <UFormField label="Name">
        <UInput
          v-model="form.name"
          required
          class="w-full"
        />
      </UFormField>
      <UFormField label="Email">
        <UInput
          v-model="form.email"
          type="email"
          required
          class="w-full"
        />
      </UFormField>
      <UFormField label="Password">
        <UInput
          v-model="form.password"
          type="password"
          required
          minlength="8"
          class="w-full"
        />
      </UFormField>
      <UFormField label="Role">
        <USelect
          v-model="form.role"
          :items="[
            { label: 'Admin', value: 'ADMIN' },
            { label: 'Manager', value: 'MANAGER' },
            { label: 'Staff', value: 'STAFF' }
          ]"
          class="w-full"
        />
      </UFormField>
      <UInput
        v-model="form.phone"
        placeholder="Phone"
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
        class="flex flex-wrap justify-between gap-2 py-3"
      >
        <div>
          <p class="font-medium">
            {{ r.name }}
          </p>
          <p class="mt-1 text-sm text-ink-muted">
            {{ r.email }} · {{ r.role }}
          </p>
        </div>
        <span class="text-sm uppercase text-ink-muted">{{ r.status }}</span>
      </li>
      <li
        v-if="!rows.length && status !== 'pending'"
        class="py-4 text-ink-muted"
      >
        No users.
      </li>
    </ul>
  </AdminPage>
</template>
