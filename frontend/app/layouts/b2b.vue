<script setup lang="ts">
const auth = useAuthStore()
const route = useRoute()
const open = ref(false)

watch(() => route.fullPath, () => {
  open.value = false
})

async function logout() {
  await auth.logout()
  await navigateTo('/login')
}

const links = computed(() => {
  const items = [
    { label: 'Orders', to: '/b2b/orders' },
    { label: 'Downline', to: '/b2b/downline' }
  ]
  if (auth.hasPermission('b2b.orders.write')) {
    items.unshift({ label: 'New order', to: '/b2b/orders/new' })
  }
  items.unshift({ label: 'Home', to: '/b2b' })
  return items
})
</script>

<template>
  <div class="min-h-dvh bg-gold-100 text-ink">
    <header class="sticky top-0 z-40 flex h-14 items-center justify-between border-b border-gold-300/70 bg-gold-100/95 px-3 md:px-4">
      <div class="flex items-center gap-2">
        <button
          type="button"
          class="rounded-md px-2 py-1.5 text-sm md:hidden"
          @click="open = !open"
        >
          Menu
        </button>
        <NuxtLink
          to="/b2b"
          class="font-display text-lg"
        >
          Trade portal
        </NuxtLink>
      </div>
      <div class="flex items-center gap-2 text-sm">
        <span class="hidden text-ink-muted sm:inline">{{ auth.user?.name }} · {{ auth.user?.role }}</span>
        <button
          type="button"
          class="rounded-md bg-gold-300/50 px-2.5 py-1.5 hover:bg-gold-300"
          @click="logout"
        >
          Logout
        </button>
      </div>
    </header>

    <div class="mx-auto flex max-w-5xl">
      <aside
        class="fixed inset-y-14 left-0 z-30 w-52 overflow-y-auto border-r border-gold-300/60 bg-gold-50 p-3 transition-transform md:static md:translate-x-0"
        :class="open ? 'translate-x-0' : '-translate-x-full md:translate-x-0'"
      >
        <nav class="flex flex-col gap-0.5">
          <NuxtLink
            v-for="l in links"
            :key="l.to"
            :to="l.to"
            class="rounded-md px-3 py-2 text-sm hover:bg-gold-200/60"
            active-class="bg-gold-300/50 font-medium"
          >
            {{ l.label }}
          </NuxtLink>
        </nav>
      </aside>
      <main class="min-w-0 flex-1 px-4 py-6 sm:px-6">
        <slot />
      </main>
    </div>
  </div>
</template>
