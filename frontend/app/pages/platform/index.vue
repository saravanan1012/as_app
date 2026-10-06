<script setup lang="ts">
definePageMeta({ layout: 'platform', middleware: ['platform'] })

const { api } = useApi()
const adminCtx = useAdminContextStore()

const { data: dash } = await useAdminAsyncData('platform-dash', () =>
  api<{
    vendors: { total: number, store_enabled_count: number, active: number }
  }>('/platform/dashboard')
)

const { data: vendorsRes, refresh } = await useAdminAsyncData('platform-vendors', () =>
  api<Array<{
    id: number
    name: string
    slug: string
    status: string
    plan?: string
    store_enabled?: boolean
    settings?: { features?: { store_enabled?: boolean } }
  }>>('/platform/vendors')
)

const vendors = computed(() => vendorsRes.value?.data || [])
const stats = computed(() => dash.value?.data)

async function toggleStore(v: { id: number }, enabled: boolean) {
  await api(`/platform/vendors/${v.id}/store`, {
    method: 'PATCH',
    body: { store_enabled: enabled }
  })
  await refresh()
}

function openAdmin(id: number) {
  adminCtx.setVendorId(id)
  navigateTo('/admin')
}
</script>

<template>
  <div>
    <div class="mb-8 flex flex-wrap items-end justify-between gap-3">
      <div>
        <h1 class="font-display text-4xl">
          Platform
        </h1>
        <p class="mt-1 text-ink-muted">
          Vendors, Store toggle, and health.
        </p>
      </div>
      <UButton
        to="/platform/vendors/new"
        size="lg"
      >
        New vendor
      </UButton>
    </div>

    <div class="mb-8 grid gap-4 sm:grid-cols-3">
      <div class="border-y border-gold-300/70 py-4">
        <p class="text-sm text-ink-muted">
          Vendors
        </p>
        <p class="font-display text-3xl">
          {{ stats?.vendors?.total ?? vendors.length }}
        </p>
      </div>
      <div class="border-y border-gold-300/70 py-4">
        <p class="text-sm text-ink-muted">
          Store enabled
        </p>
        <p class="font-display text-3xl">
          {{ stats?.vendors?.store_enabled_count ?? '—' }}
        </p>
      </div>
      <div class="border-y border-gold-300/70 py-4">
        <p class="text-sm text-ink-muted">
          Active
        </p>
        <p class="font-display text-3xl">
          {{ stats?.vendors?.active ?? vendors.filter(v => v.status === 'ACTIVE').length }}
        </p>
      </div>
    </div>

    <ul class="divide-y divide-gold-300/70 border-y border-gold-300/70">
      <li
        v-for="v in vendors"
        :key="v.id"
        class="flex flex-col gap-3 py-4 sm:flex-row sm:items-center sm:justify-between"
      >
        <div>
          <NuxtLink
            :to="`/platform/vendors/${v.id}`"
            class="font-display text-xl hover:text-gold-800"
          >
            {{ v.name }}
          </NuxtLink>
          <p class="text-sm text-ink-muted">
            {{ v.slug }} · {{ v.status }} · {{ v.plan || 'BASIC' }}
          </p>
        </div>
        <div class="flex flex-wrap items-center gap-2">
          <label class="flex items-center gap-2 text-sm">
            <USwitch
              :model-value="!!(v.store_enabled ?? v.settings?.features?.store_enabled)"
              @update:model-value="(val: boolean) => toggleStore(v, val)"
            />
            Store
          </label>
          <UButton
            size="sm"
            variant="outline"
            @click="openAdmin(v.id)"
          >
            Open admin
          </UButton>
          <UButton
            size="sm"
            color="neutral"
            variant="ghost"
            :to="`/platform/vendors/${v.id}`"
          >
            Details
          </UButton>
        </div>
      </li>
    </ul>
  </div>
</template>
