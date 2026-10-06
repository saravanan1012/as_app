<script setup lang="ts">
definePageMeta({ layout: 'admin', middleware: ['admin'] })

const { api } = useApi()

const { data, status } = await useAdminAsyncData('admin-audit', () =>
  api<{ data: Array<Record<string, any>> }>('/audit-logs?page_size=100')
)
const rows = computed(() => data.value?.data?.data || [])
</script>

<template>
  <AdminPage
    title="Audit"
    description="Change history for this vendor"
  >
    <p
      v-if="status === 'pending'"
      class="text-ink-muted"
    >
      Loading…
    </p>
    <ul class="divide-y divide-gold-300/60 border-y border-gold-300/60">
      <li
        v-for="r in rows"
        :key="r.id"
        class="py-3 text-sm"
      >
        <div class="flex flex-wrap justify-between gap-2">
          <span class="font-medium">{{ r.action }} · {{ r.entity_type }} #{{ r.entity_id }}</span>
          <span class="text-ink-muted">{{ r.created_at }}</span>
        </div>
        <p class="mt-1 text-ink-muted">
          {{ r.user_name || 'system' }}
        </p>
      </li>
      <li
        v-if="!rows.length && status !== 'pending'"
        class="py-4 text-ink-muted"
      >
        No audit entries.
      </li>
    </ul>
  </AdminPage>
</template>
