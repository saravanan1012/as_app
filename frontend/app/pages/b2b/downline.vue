<script setup lang="ts">
definePageMeta({ layout: 'b2b', middleware: ['b2b'] })

const { api } = useApi()
const { data, status } = await useAsyncData('b2b-downline', () =>
  api<{ data: Array<Record<string, any>> }>('/b2b/downline')
)
const rows = computed(() => data.value?.data?.data || [])
</script>

<template>
  <div>
    <h1 class="font-display text-3xl">
      Downline
    </h1>
    <p
      v-if="status === 'pending'"
      class="mt-6 text-ink-muted"
    >
      Loading…
    </p>
    <ul
      v-else
      class="mt-6 divide-y divide-gold-300/60 border-y border-gold-300/60"
    >
      <li
        v-for="r in rows"
        :key="r.id"
        class="flex justify-between gap-3 py-3 text-sm"
      >
        <div>
          <p class="font-medium">
            {{ r.name }}
          </p>
          <p class="text-ink-muted">
            {{ r.party_type }} · {{ r.phone || r.email || '—' }}
          </p>
        </div>
        <span class="text-ink-muted">#{{ r.id }}</span>
      </li>
      <li
        v-if="!rows.length"
        class="py-8 text-ink-muted"
      >
        No downline parties yet.
      </li>
    </ul>
  </div>
</template>
