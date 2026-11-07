// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  modules: [
    '@nuxt/eslint',
    '@nuxt/ui',
    '@pinia/nuxt'
  ],

  // DevTools can aggravate RouterView DOM races during HMR; re-enable if needed
  devtools: { enabled: false },

  css: ['~/assets/css/main.css'],

  colorMode: {
    preference: 'light',
    fallback: 'light'
  },

  runtimeConfig: {
    public: {
      apiBase: process.env.NUXT_PUBLIC_API_BASE || '/api',
      vendorSlug: process.env.NUXT_PUBLIC_VENDOR_SLUG || 'as-demo',
      appUrl: process.env.NUXT_PUBLIC_APP_URL || 'http://localhost:3000'
    }
  },

  nitro: {
    routeRules: {
      '/api/**': {
        proxy: `${process.env.NUXT_API_PROXY || 'http://localhost:8000'}/api/**`
      }
    }
  },

  app: {
    head: {
      htmlAttrs: { lang: 'en' },
      title: 'AS Signature',
      meta: [{ name: 'viewport', content: 'width=device-width, initial-scale=1' }],
      link: [
        { rel: 'icon', type: 'image/x-icon', href: '/favicon.ico' },
        { rel: 'icon', type: 'image/png', sizes: '32x32', href: '/favicon-32x32.png' },
        { rel: 'apple-touch-icon', sizes: '180x180', href: '/apple-touch-icon.png' }
      ]
    },
    // Explicitly off — transitions + Nuxt UI Teleports break admin RouterView updates
    pageTransition: false,
    layoutTransition: false
  },

  compatibilityDate: '2026-06-30',

  eslint: {
    config: {
      stylistic: {
        commaDangle: 'never',
        braceStyle: '1tbs'
      }
    }
  }
})
