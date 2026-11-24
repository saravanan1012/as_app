<script setup lang="ts">
import { landingFeatures, landingProductStory } from '~/utils/landingFeatures'

const root = ref<HTMLElement | null>(null)
const visible = ref(false)
let io: IntersectionObserver | null = null

onMounted(() => {
  const el = root.value
  if (!el) return

  if (typeof IntersectionObserver === 'undefined') {
    visible.value = true
    return
  }

  io = new IntersectionObserver(
    ([entry]) => {
      if (entry?.isIntersecting) {
        visible.value = true
        io?.disconnect()
        io = null
      }
    },
    { rootMargin: '0px 0px -12% 0px', threshold: 0.15 }
  )
  io.observe(el)
})

onUnmounted(() => {
  io?.disconnect()
  io = null
})
</script>

<template>
  <section
    ref="root"
    class="landing-features mx-auto max-w-6xl px-4 py-16 sm:px-6 sm:py-24"
    :class="{ 'landing-features--visible': visible }"
  >
    <div class="landing-features__grid">
      <div class="landing-features__story">
        <p class="landing-features__eyebrow font-display text-sm tracking-[0.14em] uppercase text-gold-800">
          {{ landingProductStory.eyebrow }}
        </p>
        <h2 class="landing-features__headline mt-3 font-display text-3xl text-ink sm:text-4xl md:text-5xl">
          {{ landingProductStory.headline }}
        </h2>
        <span
          class="landing-features__rule mt-5 block h-px w-16 origin-left bg-gold-600"
          aria-hidden="true"
        />
        <p class="landing-features__body mt-5 max-w-md text-base leading-relaxed text-ink-muted sm:text-lg">
          {{ landingProductStory.body }}
        </p>

        <figure class="landing-features__figure mt-10 overflow-hidden">
          <img
            :src="landingProductStory.image"
            :alt="landingProductStory.imageAlt"
            class="landing-features__img h-full w-full object-cover"
            loading="lazy"
            decoding="async"
          >
        </figure>
      </div>

      <ol class="landing-features__list mt-12 lg:mt-0">
        <li
          v-for="(feature, i) in landingFeatures"
          :key="feature.id"
          class="landing-features__item border-t border-gold-300/80 py-5 last:border-b"
          :style="{ '--feature-i': i }"
        >
          <div class="flex gap-4 sm:gap-5">
            <span
              class="landing-features__index font-display text-sm tabular-nums text-gold-700"
              aria-hidden="true"
            >
              {{ String(i + 1).padStart(2, '0') }}
            </span>
            <div>
              <p class="font-display text-xl text-ink sm:text-2xl">
                {{ feature.title }}
              </p>
              <p class="mt-1.5 max-w-sm text-sm leading-relaxed text-ink-muted sm:text-base">
                {{ feature.detail }}
              </p>
            </div>
          </div>
        </li>
      </ol>
    </div>
  </section>
</template>
