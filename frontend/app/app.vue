<script setup lang="ts">
const vendor = useVendorStore()

useHead({
  link: [
    { rel: 'preconnect', href: 'https://fonts.googleapis.com' },
    { rel: 'preconnect', href: 'https://fonts.gstatic.com', crossorigin: '' },
    {
      rel: 'stylesheet',
      href: 'https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,700&family=Source+Sans+3:wght@400;500;600;700&display=swap'
    }
  ]
})

// Reactive getters — do NOT call useSeoMeta inside watchEffect (causes update races).
useSeoMeta({
  title: () => vendor.brandName,
  description: () => vendor.tagline || vendor.blurb || `${vendor.brandName} — botanicals & essentials`,
  ogTitle: () => vendor.brandName,
  ogDescription: () => vendor.tagline || vendor.blurb
})
</script>

<template>
  <UApp>
    <NuxtLayout>
      <!-- No :key — remounting every path fights UApp Teleports (emitsOptions / parentNode null) -->
      <NuxtPage />
    </NuxtLayout>
  </UApp>
</template>
