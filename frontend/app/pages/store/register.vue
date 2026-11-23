<script setup lang="ts">
definePageMeta({ middleware: ['store-enabled'] })

const auth = useAuthStore()
const name = ref('')
const email = ref('')
const phone = ref('')
const password = ref('')
const confirmPassword = ref('')
const showPassword = ref(false)
const showConfirmPassword = ref(false)
const error = ref('')
const loading = ref(false)

async function submit() {
  error.value = ''
  if (password.value.length < 6) {
    error.value = 'Password must be at least 6 characters.'
    return
  }
  if (password.value !== confirmPassword.value) {
    error.value = 'Password and confirmation do not match.'
    return
  }
  loading.value = true
  try {
    await auth.registerStore(
      email.value.trim(),
      password.value,
      name.value.trim(),
      phone.value.trim() || undefined
    )
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
      Customer account for Store checkout, orders, and reviews. Add a mobile to sign in with it later.
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
          autocomplete="name"
        />
      </UFormField>
      <UFormField label="Email">
        <UInput
          v-model="email"
          type="email"
          required
          size="lg"
          class="w-full"
          autocomplete="email"
        />
      </UFormField>
      <UFormField label="Mobile (optional)">
        <UInput
          v-model="phone"
          type="tel"
          size="lg"
          class="w-full"
          autocomplete="tel"
          placeholder="10-digit mobile"
        />
      </UFormField>
      <UFormField label="Password">
        <UInput
          v-model="password"
          :type="showPassword ? 'text' : 'password'"
          required
          minlength="6"
          size="lg"
          class="w-full"
          autocomplete="new-password"
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
      <UFormField label="Confirm password">
        <UInput
          v-model="confirmPassword"
          :type="showConfirmPassword ? 'text' : 'password'"
          required
          minlength="6"
          size="lg"
          class="w-full"
          autocomplete="new-password"
          :ui="{ trailing: 'pe-1' }"
        >
          <template #trailing>
            <UButton
              color="neutral"
              variant="link"
              size="sm"
              :icon="showConfirmPassword ? 'i-lucide-eye-off' : 'i-lucide-eye'"
              :aria-label="showConfirmPassword ? 'Hide confirm password' : 'Show confirm password'"
              :aria-pressed="showConfirmPassword"
              @click="showConfirmPassword = !showConfirmPassword"
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
        Register
      </UButton>
    </form>

    <p class="mt-6 text-center text-sm text-ink">
      Already have an account?
      <NuxtLink
        to="/login"
        class="font-medium text-gold-800 underline-offset-2 hover:underline"
      >
        Sign in
      </NuxtLink>
    </p>
  </div>
</template>
