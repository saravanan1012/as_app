<script setup lang="ts">
const vendor = useVendorStore()

useHead({
  link: [
    { rel: 'icon', type: 'image/x-icon', href: '/favicon.ico' },
    { rel: 'icon', type: 'image/png', sizes: '32x32', href: '/favicon-32x32.png' },
    { rel: 'apple-touch-icon', sizes: '180x180', href: '/apple-touch-icon.png' },
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
  description: () => vendor.tagline || vendor.blurb || `${vendor.brandName} — cotton & organic care`,
  ogTitle: () => vendor.brandName,
  ogDescription: () => vendor.tagline || vendor.blurb,
  ogImage: '/images/logo-180.png'
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
