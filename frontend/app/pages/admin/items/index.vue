<script setup lang="ts">
definePageMeta({ layout: 'admin', middleware: ['admin'] })

const auth = useAuthStore()
const { api } = useApi()
const search = ref('')

const { data, refresh, status } = await useAdminAsyncData(
  'admin-items',
  () => {
    const q = search.value ? `?search=${encodeURIComponent(search.value)}&page_size=100` : '?page_size=100'
    return api<{ data: Array<Record<string, any>> }>(`/items${q}`)
  },
  { watch: [search] }
)
const rows = computed(() => data.value?.data?.data || [])
</script>

<template>
  <AdminPage
    title="Items"
    description="Catalog products and pricing"
  >
    <template #actions>
      <UButton
        v-if="auth.hasPermission('catalog.items.write')"
        to="/admin/items/new"
      >
        New item
      </UButton>
    </template>

    <div class="mb-6">
      <UInput
        v-model="search"
        placeholder="Search code or name"
        class="w-56"
        @keyup.enter="refresh()"
      />
    </div>

    <p
      v-if="status === 'pending'"
      class="text-ink-muted"
    >
      Loading…
    </p>

    <div class="hidden overflow-x-auto md:block">
      <table class="w-full text-left text-sm">
        <thead class="border-b border-gold-300 text-ink-muted">
          <tr>
            <th class="py-2 pr-3 font-medium">
              Code
            </th>
            <th class="py-2 pr-3 font-medium">
              Name
            </th>
            <th class="py-2 pr-3 font-medium">
              Sale
            </th>
            <th class="py-2 pr-3 font-medium">
              Online
            </th>
            <th class="py-2 pr-3 font-medium">
              Status
            </th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="r in rows"
            :key="r.id"
            class="border-b border-gold-300/50"
          >
            <td class="py-3 pr-3">
              <NuxtLink
                :to="`/admin/items/${r.id}`"
                class="font-medium text-gold-800 hover:underline"
              >
                {{ r.code }}
              </NuxtLink>
            </td>
            <td class="py-3 pr-3">
              {{ r.name }}
            </td>
            <td class="py-3 pr-3 tabular-nums">
              ₹{{ Number(r.sale_price).toFixed(0) }}
            </td>
            <td class="py-3 pr-3">
              {{ r.is_online_sale ? 'Yes' : 'No' }}
            </td>
            <td class="py-3 pr-3">
              {{ r.status }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <ul class="divide-y divide-gold-300/60 border-y border-gold-300/60 md:hidden">
      <li
        v-for="r in rows"
        :key="r.id"
        class="py-3"
      >
        <NuxtLink
          :to="`/admin/items/${r.id}`"
          class="block"
        >
          <div class="flex justify-between gap-2">
            <span class="font-medium">{{ r.name }}</span>
            <span>₹{{ Number(r.sale_price).toFixed(0) }}</span>
          </div>
          <p class="mt-1 text-sm text-ink-muted">
            {{ r.code }} · {{ r.status }}
          </p>
        </NuxtLink>
      </li>
    </ul>

    <p
      v-if="status !== 'pending' && !rows.length"
      class="mt-6 text-ink-muted"
    >
      No items yet.
    </p>
  </AdminPage>
</template>
