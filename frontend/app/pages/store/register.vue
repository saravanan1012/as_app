<script setup lang="ts">
definePageMeta({ middleware: ['store-enabled'] })

const auth = useAuthStore()
const name = ref('')
const email = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

async function submit() {
  error.value = ''
  loading.value = true
  try {
    await auth.registerStore(email.value.trim(), password.value, name.value.trim())
    await navigateTo('/store')
  } catch (e: unknown) {
    error.value = (e as { data?: { message?: string } })?.data?.message || 'Registration failed'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="mx-auto max-w-md px-4 py-12">
    <h1 class="font-display text-4xl text-ink">
      Create account
    </h1>
    <p class="mt-2 text-ink-muted">
      Customer account for Store checkout and orders.
    </p>
    <form
      class="mt-8 space-y-4"
      @submit.prevent="submit"
    >
      <UFormField label="Name">
        <UInput
          v-model="name"
          required
          size="lg"
          class="w-full"
        />
      </UFormField>
      <UFormField label="Email">
        <UInput
          v-model="email"
          type="email"
          required
          size="lg"
          class="w-full"
        />
      </UFormField>
      <UFormField label="Password">
        <UInput
          v-model="password"
          type="password"
          required
          minlength="6"
          size="lg"
          class="w-full"
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
        block
        :loading="loading"
      >
        Register
      </UButton>
    </form>
  </div>
</template>
