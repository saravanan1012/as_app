<script setup lang="ts">
const auth = useAuthStore()
const { visible } = useAdminNav()
const open = ref(false)
const route = useRoute()

watch(() => route.fullPath, () => {
  open.value = false
})

async function logout() {
  await auth.logout()
  await navigateTo('/login')
}
</script>

<template>
  <div class="min-h-dvh bg-gold-100 text-ink">
    <header class="sticky top-0 z-40 flex h-14 items-center justify-between border-b border-gold-300/70 bg-gold-100/95 px-3 md:px-4">
      <div class="flex items-center gap-2">
        <button
          type="button"
          class="rounded-md px-2 py-1.5 text-sm text-ink md:hidden"
          aria-label="Menu"
          @click="open = !open"
        >
          Menu
        </button>
        <NuxtLink
          to="/admin"
          class="font-display text-lg"
        >
          Admin
        </NuxtLink>
      </div>
      <div class="flex items-center gap-2 text-sm">
        <span class="hidden text-ink-muted sm:inline">{{ auth.user?.name }}</span>
        <NuxtLink
          to="/"
          class="rounded-md px-2 py-1.5 text-ink-muted hover:text-ink"
        >
          Site
        </NuxtLink>
        <button
          type="button"
          class="rounded-md bg-gold-300/50 px-2.5 py-1.5 text-ink hover:bg-gold-300"
          @click="logout"
        >
          Logout
        </button>
      </div>
    </header>

    <div class="mx-auto flex max-w-7xl">
      <aside
        class="fixed inset-y-14 left-0 z-30 w-60 overflow-y-auto border-r border-gold-300/60 bg-gold-50 p-3 transition-transform md:static md:translate-x-0"
        :class="open ? 'translate-x-0' : '-translate-x-full md:translate-x-0'"
      >
        <nav class="flex flex-col gap-0.5">
          <NuxtLink
            v-for="item in visible"
            :key="item.to"
            :to="item.to"
            class="rounded-md px-3 py-2.5 text-sm text-ink-muted hover:bg-gold-300/40 hover:text-ink"
            active-class="bg-gold-300/60 text-ink font-medium"
          >
            {{ item.label }}
          </NuxtLink>
        </nav>
      </aside>
      <button
        v-if="open"
        type="button"
        class="fixed inset-0 z-20 bg-ink/30 md:hidden"
        aria-label="Close menu"
        @click="open = false"
      />
      <main class="min-w-0 flex-1 px-3 py-5 sm:px-6 sm:py-8">
        <slot />
      </main>
    </div>
  </div>
</template>
