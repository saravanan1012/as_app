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
      <p class="mt-1">
        Crafted with care · {{ new Date().getFullYear() }}
      </p>
    </footer>
  </div>
</template>
