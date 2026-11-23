<script setup lang="ts">
const props = withDefaults(
  defineProps<{
    salePrice: number
    mrp?: number | null
    size?: 'sm' | 'md' | 'lg'
  }>(),
  { mrp: null, size: 'md' }
)

const sale = computed(() => Number(props.salePrice || 0))
const compare = computed(() => Number(props.mrp || 0))
const showStrike = computed(() => compare.value > sale.value + 0.004)

const saleClass = computed(() => {
  if (props.size === 'lg') return 'text-2xl font-semibold text-gold-800'
  if (props.size === 'sm') return 'text-sm text-ink-muted'
  return 'text-ink'
})
</script>

<template>
  <span class="inline-flex flex-wrap items-baseline gap-x-2 gap-y-0.5">
    <span
      v-if="showStrike"
      class="text-ink-muted line-through"
      :class="size === 'lg' ? 'text-base' : 'text-sm'"
    >₹{{ compare.toFixed(0) }}</span>
    <span :class="saleClass">₹{{ sale.toFixed(0) }}</span>
  </span>
</template>
