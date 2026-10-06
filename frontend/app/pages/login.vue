<script setup lang="ts">
const auth = useAuthStore()
const { resolveHome } = useRedirect()
const email = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

async function submit() {
  error.value = ''
  loading.value = true
  try {
    const user = await auth.login(email.value.trim(), password.value)
    await navigateTo(resolveHome(user))
  } catch (e: unknown) {
    error.value = (e as { data?: { message?: string } })?.data?.message || 'Login failed'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="mx-auto flex min-h-[70dvh] max-w-md flex-col justify-center px-4 py-12">
    <h1 class="font-display text-4xl text-ink">
      Login
    </h1>
    <p class="mt-2 text-ink-muted">
      Staff and customers use the same sign-in. You’ll be sent to the right home.
    </p>

    <form
      class="mt-8 space-y-4"
      @submit.prevent="submit"
    >
      <UFormField label="Email">
        <UInput
          v-model="email"
          type="email"
          required
          size="lg"
          class="w-full"
          autocomplete="username"
        />
      </UFormField>
      <UFormField label="Password">
        <UInput
          v-model="password"
          type="password"
          required
          size="lg"
          class="w-full"
          autocomplete="current-password"
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
        Sign in
      </UButton>
    </form>

    <p class="mt-6 text-sm text-ink-muted">
      New to the Store?
      <NuxtLink
        to="/store/register"
        class="text-gold-800 underline-offset-2 hover:underline"
      >
        Create a customer account
      </NuxtLink>
    </p>
  </div>
</template>
