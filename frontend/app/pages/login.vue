<script setup lang="ts">
const auth = useAuthStore()
const { resolveHome } = useRedirect()
const identifier = ref('')
const password = ref('')
const showPassword = ref(false)
const error = ref('')
const loading = ref(false)

async function submit() {
  error.value = ''
  const value = identifier.value.trim()
  if (!value) {
    error.value = 'Enter your email or mobile number.'
    return
  }
  loading.value = true
  try {
    // API field is still named `email` for compat; value may be email or mobile
    const user = await auth.login(value, password.value)
    await navigateTo(resolveHome(user))
  } catch (e: unknown) {
    const msg = (e as { data?: { message?: string, error?: string } })?.data
    error.value = msg?.message || msg?.error || 'Login failed'
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
      Use your email or 10-digit mobile number with your password.
    </p>

    <form
      class="mt-8 space-y-4"
      novalidate
      @submit.prevent="submit"
    >
      <div>
        <label
          for="login-identifier"
          class="mb-1.5 block text-sm font-medium text-ink"
        >
          Mobile or email
        </label>
        <input
          id="login-identifier"
          v-model="identifier"
          type="text"
          inputmode="text"
          name="identifier"
          required
          autocomplete="username"
          placeholder="9000000040 or you@email.com"
          class="w-full rounded-md border border-gold-300/70 bg-white px-3 py-2.5 text-base text-ink outline-none ring-gold-600 focus:ring-2"
        >
      </div>
      <UFormField
        label="Password"
        name="password"
      >
        <UInput
          v-model="password"
          :type="showPassword ? 'text' : 'password'"
          name="password"
          required
          size="lg"
          class="w-full"
          autocomplete="current-password"
          :ui="{ trailing: 'pe-1' }"
        >
          <template #trailing>
            <UButton
              color="neutral"
              variant="link"
              size="sm"
              :icon="showPassword ? 'i-lucide-eye-off' : 'i-lucide-eye'"
              :aria-label="showPassword ? 'Hide password' : 'Show password'"
              :aria-pressed="showPassword"
              @click="showPassword = !showPassword"
            />
          </template>
        </UInput>
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
