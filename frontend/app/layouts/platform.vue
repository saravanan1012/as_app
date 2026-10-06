<script setup lang="ts">
const auth = useAuthStore()

async function logout() {
  await auth.logout()
  await navigateTo('/login')
}
</script>

<template>
  <div class="min-h-dvh bg-gold-100 text-ink">
    <header class="sticky top-0 z-40 flex h-14 items-center justify-between border-b border-gold-300/70 bg-gold-100/90 px-4 backdrop-blur">
      <NuxtLink
        to="/platform"
        class="font-display text-lg"
      >
        Platform
      </NuxtLink>
      <div class="flex items-center gap-2">
        <UButton
          to="/"
          size="sm"
          color="neutral"
          variant="ghost"
        >
          Site
        </UButton>
        <UButton
          size="sm"
          color="neutral"
          variant="soft"
          @click="logout"
        >
          Logout
        </UButton>
      </div>
    </header>
    <main class="mx-auto max-w-6xl px-3 py-6 sm:px-6 sm:py-10">
      <slot />
    </main>
  </div>
</template>
