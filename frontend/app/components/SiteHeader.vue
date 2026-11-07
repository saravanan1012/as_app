<script setup lang="ts">
const vendor = useVendorStore()
const auth = useAuthStore()
const cart = useCartStore()
const { resolveHome } = useRedirect()

const isCustomer = computed(() => auth.user?.role === 'CUSTOMER')

const links = computed(() => {
  const items = [
    { label: 'Products', to: '/products' },
    { label: 'Contact', to: '/contact' }
  ]
  if (vendor.storeEnabled) {
    items.splice(1, 0, { label: 'Online Store', to: '/store' })
  }
  return items
})
</script>

<template>
  <header class="sticky top-0 z-40 border-b border-gold-300/60 bg-gold-100/85 backdrop-blur-md">
    <div class="mx-auto flex h-14 max-w-6xl items-center justify-between gap-4 px-4 sm:h-16 sm:px-6">
      <NuxtLink
        to="/"
        class="flex items-center gap-2 text-ink"
        :aria-label="vendor.brandName"
      >
        <img
          src="/images/logo-header.png"
          alt=""
          width="40"
          height="40"
          class="h-9 w-9 shrink-0 object-contain sm:h-10 sm:w-10"
        >
        <span class="font-display hidden text-xl tracking-tight sm:inline sm:text-2xl">
          {{ vendor.brandName }}
        </span>
      </NuxtLink>

      <nav class="hidden items-center gap-6 text-sm font-medium text-ink-muted md:flex">
        <NuxtLink
          v-for="link in links"
          :key="link.to"
          :to="link.to"
          class="transition-colors hover:text-ink"
          active-class="text-ink"
        >
          {{ link.label }}
        </NuxtLink>
      </nav>

      <div class="flex items-center gap-2">
        <NuxtLink
          v-if="vendor.storeEnabled"
          to="/store/cart"
          class="relative inline-flex h-10 items-center justify-center rounded-full px-2 text-sm font-medium text-ink transition hover:bg-gold-300/50"
          aria-label="Cart"
        >
          Cart
          <span
            v-if="cart.count"
            class="ml-1 flex h-5 min-w-5 items-center justify-center rounded-full bg-gold-700 px-1 text-[11px] font-semibold text-white"
          >
            {{ cart.count }}
          </span>
        </NuxtLink>

        <UButton
          v-if="auth.isLoggedIn"
          color="neutral"
          variant="ghost"
          size="sm"
          :to="isCustomer ? '/store/orders' : resolveHome()"
        >
          {{ isCustomer ? 'My orders' : 'Account' }}
        </UButton>
        <UButton
          v-else
          to="/login"
          size="sm"
          color="primary"
        >
          Login
        </UButton>
      </div>
    </div>

    <nav class="flex gap-4 overflow-x-auto border-t border-gold-300/40 px-4 py-2 text-sm text-ink-muted md:hidden">
      <NuxtLink
        v-for="link in links"
        :key="link.to"
        :to="link.to"
        class="whitespace-nowrap"
      >
        {{ link.label }}
      </NuxtLink>
    </nav>
  </header>
</template>
