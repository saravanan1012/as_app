<script setup lang="ts">
definePageMeta({ layout: 'admin', middleware: ['admin'] })

const route = useRoute()
const { api } = useApi()
const id = computed(() => Number(route.params.id))

const { data } = await useAdminAsyncData(() => `cust-${id.value}`, () =>
  api<{
    id: number
    name: string
    party_type: string
    acquisition_source?: string
    phone?: string
    email?: string
    gstin?: string
    parent_id?: number
    children?: Array<{ id: number, name: string, party_type: string }>
    addresses?: Array<{ street?: string, city?: string, state?: string, zip?: string }>
  }>(`/customers/${id.value}`)
)

const c = computed(() => data.value?.data)
</script>

<template>
  <AdminPage
    v-if="c"
    :title="c.name"
    :description="`${c.party_type}${c.acquisition_source ? ' · ' + c.acquisition_source : ''}`"
  >
    <dl class="grid gap-3 text-sm sm:grid-cols-2">
      <div>
        <dt class="text-ink-muted">
          Phone
        </dt>
        <dd>{{ c.phone || '—' }}</dd>
      </div>
      <div>
        <dt class="text-ink-muted">
          Email
        </dt>
        <dd>{{ c.email || '—' }}</dd>
      </div>
      <div>
        <dt class="text-ink-muted">
          GSTIN
        </dt>
        <dd>{{ c.gstin || '—' }}</dd>
      </div>
      <div>
        <dt class="text-ink-muted">
          Parent
        </dt>
        <dd>
          <NuxtLink
            v-if="c.parent_id"
            :to="`/admin/customers/${c.parent_id}`"
            class="text-gold-800 underline"
          >
            #{{ c.parent_id }}
          </NuxtLink>
          <span v-else>—</span>
        </dd>
      </div>
    </dl>

    <h2 class="font-display mt-8 text-xl">
      Address
    </h2>
    <p class="mt-2 text-sm text-ink-muted">
      <template v-if="c.addresses?.length">
        {{ [c.addresses[0].street, c.addresses[0].city, c.addresses[0].state, c.addresses[0].zip].filter(Boolean).join(', ') }}
      </template>
      <template v-else>
        None on file
      </template>
    </p>

    <h2 class="font-display mt-8 text-xl">
      Downline
    </h2>
    <ul class="mt-3 divide-y divide-gold-300/60 border-y border-gold-300/60">
      <li
        v-for="ch in c.children || []"
        :key="ch.id"
        class="flex justify-between py-3 text-sm"
      >
        <NuxtLink
          :to="`/admin/customers/${ch.id}`"
          class="text-gold-800 hover:underline"
        >
          {{ ch.name }}
        </NuxtLink>
        <span class="text-ink-muted">{{ ch.party_type }}</span>
      </li>
      <li
        v-if="!(c.children || []).length"
        class="py-4 text-ink-muted"
      >
        No children.
      </li>
    </ul>
  </AdminPage>
</template>
