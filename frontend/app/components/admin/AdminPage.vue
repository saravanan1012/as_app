<script setup lang="ts">
defineProps<{
  title: string
  description?: string
}>()
</script>

<template>
  <div>
    <div class="mb-6 flex flex-wrap items-end justify-between gap-3">
      <div>
        <h1 class="font-display text-3xl text-ink">
          {{ title }}
        </h1>
        <p
          v-if="description"
          class="mt-1 text-sm text-ink-muted"
        >
          {{ description }}
        </p>
      </div>
      <div class="flex flex-wrap gap-2">
        <slot name="actions" />
      </div>
    </div>
    <slot />
  </div>
</template>
