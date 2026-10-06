<script setup lang="ts">
definePageMeta({ layout: 'admin', middleware: ['admin'] })

const auth = useAuthStore()
const { api } = useApi()
const partyType = ref('ALL')
const acquisition = ref('ALL')
const search = ref('')

const query = computed(() => {
  const p = new URLSearchParams()
  if (partyType.value && partyType.value !== 'ALL') p.set('party_type', partyType.value)
  if (acquisition.value && acquisition.value !== 'ALL') p.set('acquisition_source', acquisition.value)
  if (search.value) p.set('search', search.value)
  p.set('page_size', '100')
  return p.toString()
})

const { data, refresh, status } = await useAdminAsyncData(
  'admin-customers',
  () => api<{ data: Array<Record<string, any>> }>(`/customers?${query.value}`),
  { watch: [query] }
)
const rows = computed(() => data.value?.data?.data || [])
</script>

<template>
  <AdminPage
    title="Customers"
    description="Distributor → Dealer → Retailer → Customer hierarchy"
  >
    <template #actions>
      <UButton
        v-if="auth.hasPermission('customers.write')"
        to="/admin/customers/new"
      >
        New party
      </UButton>
    </template>

    <div class="mb-6 flex flex-wrap gap-2">
      <USelect
        v-model="partyType"
        :items="[
          { label: 'All types', value: 'ALL' },
          { label: 'Distributor', value: 'DISTRIBUTOR' },
          { label: 'Dealer', value: 'DEALER' },
          { label: 'Retailer', value: 'RETAILER' },
          { label: 'Customer', value: 'CUSTOMER' }
        ]"
        class="w-40"
      />
      <USelect
        v-model="acquisition"
        :items="[
          { label: 'All sources', value: 'ALL' },
          { label: 'Online', value: 'ONLINE' },
          { label: 'Walk-in', value: 'WALK_IN' },
          { label: 'FB lead', value: 'FB_LEAD' },
          { label: 'Referral', value: 'REFERRAL' },
          { label: 'Phone', value: 'PHONE' },
          { label: 'Other', value: 'OTHER' }
        ]"
        class="w-40"
      />
      <UInput
        v-model="search"
        placeholder="Search"
        class="w-48"
        @keyup.enter="refresh()"
      />
    </div>

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
        class="py-3"
      >
        <NuxtLink
          :to="`/admin/customers/${r.id}`"
          class="block"
        >
          <div class="flex flex-wrap items-baseline justify-between gap-2">
            <span class="font-display text-lg">{{ r.name }}</span>
            <span class="text-xs uppercase tracking-wide text-gold-800">{{ r.party_type }}</span>
          </div>
          <p class="mt-1 text-sm text-ink-muted">
            {{ r.acquisition_source || '—' }}
            <span v-if="r.parent_id"> · parent #{{ r.parent_id }}</span>
            <span v-if="r.phone"> · {{ r.phone }}</span>
          </p>
        </NuxtLink>
      </li>
      <li
        v-if="!rows.length && status !== 'pending'"
        class="py-6 text-ink-muted"
      >
        No parties match.
      </li>
    </ul>
  </AdminPage>
</template>
