<script setup lang="ts">
definePageMeta({ layout: 'platform', middleware: ['platform'] })

const { api } = useApi()
const form = reactive({
  name: '',
  slug: '',
  plan: 'BASIC',
  admin_email: '',
  admin_name: '',
  admin_password: 'User@123'
})
const error = ref('')
const loading = ref(false)

watch(() => form.name, (n) => {
  if (!form.slug) {
    form.slug = n.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '').slice(0, 80)
  }
})

async function submit() {
  error.value = ''
  loading.value = true
  try {
    const res = await api<{ id: number }>('/platform/vendors', {
      method: 'POST',
      body: form
    })
    await navigateTo(`/platform/vendors/${res.data.id}`)
  } catch (e: unknown) {
    error.value = (e as { data?: { message?: string } })?.data?.message || 'Create failed'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="max-w-lg">
    <h1 class="font-display text-3xl">
      New vendor
    </h1>
    <form
      class="mt-8 space-y-4"
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
      <UFormField label="Slug">
        <UInput
          v-model="form.slug"
          required
          class="w-full"
          size="lg"
        />
      </UFormField>
      <UFormField label="Admin email">
        <UInput
          v-model="form.admin_email"
          type="email"
          class="w-full"
          size="lg"
        />
      </UFormField>
      <UFormField label="Admin name">
        <UInput
          v-model="form.admin_name"
          class="w-full"
          size="lg"
        />
      </UFormField>
      <UFormField label="Admin password">
        <UInput
          v-model="form.admin_password"
          type="password"
          class="w-full"
          size="lg"
        />
      </UFormField>
      <p
        v-if="error"
        class="text-sm text-red-700"
      >
        {{ error }}
      </p>
      <UButton
        type="submit"
        size="xl"
        :loading="loading"
      >
        Create
      </UButton>
    </form>
  </div>
</template>
