<script setup lang="ts">
import type { LandingMedia } from '~/utils/landingMedia'
import { landingGallery } from '~/utils/landingMedia'

const items = landingGallery
const active = ref<number | null>(null)

function openAt(i: number) {
  active.value = i
}

function onVideoEnter(e: Event) {
  const el = e.currentTarget as HTMLElement
  const video = el.querySelector('video')
  if (video) void video.play().catch(() => {})
}

function onVideoLeave(e: Event) {
  const el = e.currentTarget as HTMLElement
  const video = el.querySelector('video')
  if (video) {
    video.pause()
    video.currentTime = 0
  }
}

function spanClass(item: LandingMedia) {
  if (item.span === 'portrait') return 'landing-mosaic__cell--portrait'
  if (item.span === 'tall') return 'landing-mosaic__cell--tall'
  if (item.span === 'wide') return 'landing-mosaic__cell--wide'
  return 'landing-mosaic__cell--square'
}
</script>

<template>
  <section class="landing-gallery mx-auto max-w-6xl px-4 py-16 sm:px-6 sm:py-24">
    <div class="max-w-2xl">
      <h2 class="font-display text-3xl text-ink sm:text-4xl">
        In the studio
      </h2>
      <p class="mt-3 text-ink-muted">
        Product stills and motion from our organic care line — tap any frame to open.
      </p>
    </div>

    <div class="landing-mosaic mt-10">
      <button
        v-for="(item, i) in items"
        :key="item.id"
        type="button"
        class="landing-mosaic__cell group"
        :class="[spanClass(item), `landing-reveal landing-reveal--${(i % 5) + 1}`]"
        :aria-label="`Open ${item.alt}`"
        @click="openAt(i)"
        @mouseenter="item.type === 'video' && onVideoEnter($event)"
        @mouseleave="item.type === 'video' && onVideoLeave($event)"
      >
        <img
          v-if="item.type === 'image'"
          :src="item.src"
          :alt="item.alt"
          class="landing-mosaic__media"
          loading="lazy"
          decoding="async"
        >
        <template v-else>
          <video
            :src="item.src"
            :poster="item.poster"
            class="landing-mosaic__media"
            muted
            loop
            playsinline
            preload="metadata"
          />
          <span class="landing-mosaic__play" aria-hidden="true">▶</span>
        </template>
        <span class="landing-mosaic__veil" />
      </button>
    </div>

    <LandingLightbox
      v-model="active"
      :items="items"
    />
  </section>
</template>
