<script setup lang="ts">
import { landingHeroPoster, landingHeroVideo } from '~/utils/landingMedia'

const vendor = useVendorStore()
const { api } = useApi()

const { data: productsRes } = await useAsyncData('home-products', () =>
  api<{ data: Array<{ id: number, name: string, description?: string, sale_price: number, primary_image?: string }> }>('/public/products?page_size=4')
)

const highlights = computed(() => productsRes.value?.data?.data || [])

const heroVideoEl = ref<HTMLVideoElement | null>(null)
const videoReady = ref(false)

onMounted(() => {
  const v = heroVideoEl.value
  if (!v) return
  v.muted = true
  void v.play().then(() => {
    videoReady.value = true
  }).catch(() => {
    videoReady.value = false
  })
})
</script>

<template>
  <div>
    <!-- Full-bleed cinematic hero -->
    <section class="relative min-h-[100dvh] w-full overflow-hidden text-gold-100">
      <div class="absolute inset-0">
        <img
          :src="landingHeroPoster"
          alt=""
          class="landing-hero-poster absolute inset-0 h-full w-full object-cover"
          :class="{ 'opacity-0': videoReady }"
          aria-hidden="true"
        >
        <video
          ref="heroVideoEl"
          class="absolute inset-0 h-full w-full object-cover"
          :poster="landingHeroPoster"
          :src="landingHeroVideo"
          muted
          loop
          playsinline
          autoplay
          preload="metadata"
        />
        <div class="landing-hero-scrim absolute inset-0" />
      </div>

      <div class="relative mx-auto flex min-h-[100dvh] max-w-6xl flex-col justify-end px-4 pb-16 pt-28 sm:px-6 sm:pb-24">
        <p class="anim-rise font-display text-5xl leading-[0.95] tracking-tight text-white sm:text-7xl md:text-8xl">
          {{ vendor.brandName }}
        </p>
        <h1 class="anim-rise-delay mt-5 max-w-xl text-lg font-medium text-gold-100 sm:text-2xl">
          {{ vendor.tagline || 'Plant-based essentials, thoughtfully made' }}
        </h1>
        <p class="anim-rise-delay-2 mt-3 max-w-md text-sm leading-relaxed text-gold-200/90 sm:text-base">
          {{ vendor.blurb || 'Explore our botanical line — crafted for daily rituals.' }}
        </p>
        <div class="anim-rise-delay-2 mt-8 flex flex-wrap gap-3">
          <UButton
            to="/products"
            size="xl"
            color="neutral"
            class="bg-white text-ink hover:bg-gold-100"
          >
            View products
          </UButton>
          <UButton
            v-if="vendor.storeEnabled"
            to="/store"
            size="xl"
            color="primary"
            variant="solid"
          >
            Shop the Store
          </UButton>
          <UButton
            to="/contact"
            size="xl"
            color="neutral"
            variant="ghost"
            class="text-white hover:bg-white/10"
          >
            Contact
          </UButton>
        </div>
      </div>
    </section>

    <LandingGallery />

    <section class="mx-auto max-w-6xl px-4 py-16 sm:px-6 sm:py-24">
      <div class="max-w-2xl">
        <h2 class="font-display text-3xl text-ink sm:text-4xl">
          Our essentials
        </h2>
        <p class="mt-3 text-ink-muted">
          A closer look at what we make — information first, shopping optional.
        </p>
      </div>

      <ul class="mt-10 divide-y divide-gold-300/70 border-y border-gold-300/70">
        <li
          v-for="(p, i) in highlights"
          :key="p.id"
        >
          <NuxtLink
            :to="`/products/${p.id}`"
            class="group flex flex-col gap-2 py-6 transition sm:flex-row sm:items-baseline sm:justify-between"
            :class="i === 0 ? 'anim-rise' : ''"
          >
            <span class="font-display text-2xl text-ink group-hover:text-gold-800">
              {{ p.name }}
            </span>
            <span class="max-w-md text-sm text-ink-muted line-clamp-2">
              {{ p.description || 'Learn more about this product' }}
            </span>
          </NuxtLink>
        </li>
        <li
          v-if="!highlights.length"
          class="py-10 text-ink-muted"
        >
          Product stories will appear here once the catalog is published.
        </li>
      </ul>

      <div class="mt-8">
        <UButton
          to="/products"
          variant="outline"
          color="primary"
          trailing-icon="i-lucide-arrow-right"
        >
          All products
        </UButton>
      </div>
    </section>
  </div>
</template>
