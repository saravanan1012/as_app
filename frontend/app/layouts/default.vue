<script setup lang="ts">
const vendor = useVendorStore()
</script>

<template>
  <div class="flex min-h-dvh flex-col">
    <SiteHeader />
    <main class="flex-1">
      <slot />
    </main>
    <footer class="border-t border-gold-300/50 px-4 py-8 text-center text-sm text-ink-muted">
      <p class="font-display text-base text-ink">
        {{ vendor.brandName }}
      </p>
      <nav class="mt-3 flex flex-wrap items-center justify-center gap-x-4 gap-y-1">
        <NuxtLink
          to="/privacy"
          class="transition-colors hover:text-ink"
        >
          Privacy
        </NuxtLink>
        <NuxtLink
          to="/terms"
          class="transition-colors hover:text-ink"
        >
          Terms
        </NuxtLink>
        <NuxtLink
          to="/refund"
          class="transition-colors hover:text-ink"
        >
          Refunds
        </NuxtLink>
        <NuxtLink
          to="/contact"
          class="transition-colors hover:text-ink"
        >
          Contact
        </NuxtLink>
      </nav>
      <p class="mt-3">
        Crafted with care · {{ new Date().getFullYear() }}
      </p>
    </footer>
  </div>
</template>
