<script setup lang="ts">
import type { LandingMedia } from '~/utils/landingMedia'

const props = defineProps<{
  items: LandingMedia[]
  modelValue: number | null
}>()

const emit = defineEmits<{
  'update:modelValue': [value: number | null]
}>()

const open = computed({
  get: () => props.modelValue !== null,
  set: (v: boolean) => {
    if (!v) emit('update:modelValue', null)
  }
})

const index = computed(() => props.modelValue ?? 0)
const current = computed(() => props.items[index.value] || null)

const dialogRef = ref<HTMLElement | null>(null)
const videoRef = ref<HTMLVideoElement | null>(null)

function close() {
  emit('update:modelValue', null)
}

function prev() {
  if (!props.items.length) return
  const next = (index.value - 1 + props.items.length) % props.items.length
  emit('update:modelValue', next)
}

function next() {
  if (!props.items.length) return
  emit('update:modelValue', (index.value + 1) % props.items.length)
}

function onKey(e: KeyboardEvent) {
  if (!open.value) return
  if (e.key === 'Escape') close()
  if (e.key === 'ArrowLeft') prev()
  if (e.key === 'ArrowRight') next()
}

watch(open, async (isOpen) => {
  if (import.meta.server) return
  if (isOpen) {
    document.body.style.overflow = 'hidden'
    await nextTick()
    dialogRef.value?.focus()
  } else {
    document.body.style.overflow = ''
  }
})

watch(current, async () => {
  await nextTick()
  if (current.value?.type === 'video' && videoRef.value) {
    videoRef.value.currentTime = 0
    void videoRef.value.play().catch(() => {})
  }
})

onMounted(() => {
  window.addEventListener('keydown', onKey)
})
onBeforeUnmount(() => {
  window.removeEventListener('keydown', onKey)
  document.body.style.overflow = ''
  // Avoid Teleport/DOM race if parent navigates away mid-update
  if (props.modelValue !== null) emit('update:modelValue', null)
})
</script>

<template>
  <Teleport to="body">
    <Transition name="lb">
      <div
        v-if="open && current"
        ref="dialogRef"
        class="landing-lightbox"
        role="dialog"
        aria-modal="true"
        :aria-label="current.alt"
        tabindex="-1"
        @click.self="close"
      >
        <button
          type="button"
          class="landing-lightbox__close"
          aria-label="Close"
          @click="close"
        >
          ✕
        </button>

        <button
          type="button"
          class="landing-lightbox__nav landing-lightbox__nav--prev"
          aria-label="Previous"
          @click="prev"
        >
          ‹
        </button>

        <div class="landing-lightbox__stage">
          <img
            v-if="current.type === 'image'"
            :src="current.src"
            :alt="current.alt"
            class="landing-lightbox__media"
          >
          <video
            v-else
            ref="videoRef"
            :src="current.src"
            :poster="current.poster"
            class="landing-lightbox__media"
            controls
            playsinline
            autoplay
          />
          <p class="landing-lightbox__caption">
            {{ current.alt }}
            <span class="text-gold-300/80"> · {{ index + 1 }} / {{ items.length }}</span>
          </p>
        </div>

        <button
          type="button"
          class="landing-lightbox__nav landing-lightbox__nav--next"
          aria-label="Next"
          @click="next"
        >
          ›
        </button>
      </div>
    </Transition>
  </Teleport>
</template>
