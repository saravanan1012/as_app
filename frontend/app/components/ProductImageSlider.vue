<script setup lang="ts">
import { mediaKind } from '~/utils/mediaKind'

const props = defineProps<{
  images: Array<{ path: string, media_type?: string }>
  alt: string
  primary?: string | null
}>()

const slides = computed(() => {
  const fromGallery = (props.images || [])
    .map(i => ({
      path: i.path,
      kind: (i.media_type as 'image' | 'video' | undefined) || mediaKind(i.path)
    }))
    .filter(i => i.path)
  if (fromGallery.length) return fromGallery
  return props.primary
    ? [{ path: props.primary, kind: mediaKind(props.primary) as 'image' | 'video' }]
    : []
})

const index = ref(0)

watch(slides, (list) => {
  if (index.value >= list.length) index.value = 0
})

function prev() {
  if (!slides.value.length) return
  index.value = (index.value - 1 + slides.value.length) % slides.value.length
}

function next() {
  if (!slides.value.length) return
  index.value = (index.value + 1) % slides.value.length
}

function go(i: number) {
  index.value = i
}
</script>

<template>
  <div class="space-y-3">
    <div class="relative aspect-square overflow-hidden bg-gradient-to-br from-gold-300 via-gold-500 to-gold-700">
      <template v-if="slides.length">
        <video
          v-if="slides[index]?.kind === 'video'"
          :key="slides[index]!.path"
          :src="slides[index]!.path"
          class="h-full w-full object-cover"
          controls
          playsinline
          preload="metadata"
        />
        <img
          v-else
          :src="slides[index]!.path"
          :alt="alt"
          class="h-full w-full object-cover transition-opacity duration-300"
        >
        <template v-if="slides.length > 1">
          <button
            type="button"
            class="absolute left-3 top-1/2 z-10 flex h-10 w-10 -translate-y-1/2 items-center justify-center rounded-full bg-white/90 text-lg text-ink shadow-sm transition hover:bg-white"
            aria-label="Previous media"
            @click="prev"
          >
            ‹
          </button>
          <button
            type="button"
            class="absolute right-3 top-1/2 z-10 flex h-10 w-10 -translate-y-1/2 items-center justify-center rounded-full bg-white/90 text-lg text-ink shadow-sm transition hover:bg-white"
            aria-label="Next media"
            @click="next"
          >
            ›
          </button>
        </template>
      </template>
    </div>

    <div
      v-if="slides.length > 1"
      class="flex gap-2 overflow-x-auto pb-1"
      role="listbox"
      :aria-label="`${alt} media`"
    >
      <button
        v-for="(slide, i) in slides"
        :key="slide.path"
        type="button"
        role="option"
        class="relative h-16 w-16 shrink-0 overflow-hidden border-2 transition sm:h-20 sm:w-20"
        :class="i === index ? 'border-gold-700' : 'border-gold-300/60 hover:border-gold-600'"
        :aria-selected="i === index"
        :aria-label="`${alt} ${slide.kind} ${i + 1}`"
        @click="go(i)"
      >
        <video
          v-if="slide.kind === 'video'"
          :src="slide.path"
          class="h-full w-full object-cover"
          muted
          playsinline
          preload="metadata"
        />
        <img
          v-else
          :src="slide.path"
          alt=""
          class="h-full w-full object-cover"
        >
        <span
          v-if="slide.kind === 'video'"
          class="pointer-events-none absolute inset-0 flex items-center justify-center bg-black/25 text-xs font-medium text-white"
        >
          ▶
        </span>
      </button>
    </div>
  </div>
</template>
