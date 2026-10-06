<script setup lang="ts">
definePageMeta({ layout: 'b2b', middleware: ['b2b'] })

const { api } = useApi()
const { data } = await useAsyncData('b2b-me', () => api<Record<string, any>>('/b2b/me'))
const me = computed(() => data.value?.data)
</script>

<template>
  <div>
    <h1 class="font-display text-3xl">
      Trade portal
    </h1>
    <p
      v-if="me"
      class="mt-2 text-ink-muted"
    >
      {{ me.party?.name }} · {{ me.party?.party_type }}
    </p>
    <div class="mt-8 flex flex-wrap gap-3">
      <UButton to="/b2b/orders">
        View orders
      </UButton>
      <UButton
        v-if="me"
        to="/b2b/orders/new"
        variant="outline"
      >
        Place order
      </UButton>
      <UButton
        to="/b2b/downline"
        variant="ghost"
      >
        Downline
      </UButton>
    </div>
  </div>
</template>
