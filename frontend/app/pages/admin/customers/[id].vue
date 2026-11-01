<script setup lang="ts">
definePageMeta({ layout: 'admin', middleware: ['admin'] })

const route = useRoute()
const auth = useAuthStore()
const { api } = useApi()
const id = computed(() => Number(route.params.id))

type PartySummary = { id: number, name: string, party_type: string, status?: string }
type PortalUser = { id: number, email: string, name: string, role: string, status: string, phone?: string }

const { data, refresh, status } = await useAdminAsyncData(() => `cust-${id.value}`, () =>
  api<{
    id: number
    name: string
    party_type: string
    acquisition_source?: string | null
    phone?: string | null
    email?: string | null
    gstin?: string | null
    status: string
    parent_id?: number | null
    user_id?: number | null
    parent?: PartySummary | null
    children?: PartySummary[]
    addresses?: Array<{ street?: string, city?: string, state?: string, zip?: string }>
    portal_user?: PortalUser | null
    allowed_child_types?: string[]
  }>(`/customers/${id.value}`)
)

const c = computed(() => data.value?.data)

const form = reactive({
  name: '',
  party_type: 'CUSTOMER',
  parent_id: null as number | null,
  acquisition_source: '' as string,
  phone: '',
  email: '',
  gstin: '',
  status: 'ACTIVE'
})
const editError = ref('')
const saving = ref(false)

const parentTypes = computed(() => {
  if (form.party_type === 'DEALER') return ['DISTRIBUTOR']
  if (form.party_type === 'RETAILER') return ['DEALER', 'DISTRIBUTOR']
  if (form.party_type === 'CUSTOMER') return ['RETAILER', 'DEALER', 'DISTRIBUTOR']
  return [] as string[]
})

const { data: parentsRes, refresh: refreshParents } = await useAdminAsyncData(
  () => `cust-parents-${id.value}-${form.party_type}`,
  async () => {
    if (!parentTypes.value.length) return { data: { data: [] as PartySummary[] } }
    const all: PartySummary[] = []
    for (const pt of parentTypes.value) {
      const res = await api<{ data: PartySummary[] }>(`/customers?party_type=${pt}&page_size=200`)
      all.push(...(res.data?.data || []).filter(p => p.id !== id.value))
    }
    return { data: { data: all } }
  },
  { watch: [parentTypes] }
)
const parents = computed(() => parentsRes.value?.data?.data || [])
const parentSelectItems = computed(() => [
  { label: 'Independent (no parent)', value: null as number | null },
  ...parents.value.map(p => ({ label: `${p.name} (${p.party_type})`, value: p.id as number | null }))
])

watch(c, (party) => {
  if (!party) return
  form.name = party.name
  form.party_type = party.party_type
  form.parent_id = party.parent_id ?? null
  form.acquisition_source = party.acquisition_source || ''
  form.phone = party.phone || ''
  form.email = party.email || ''
  form.gstin = party.gstin || ''
  form.status = party.status || 'ACTIVE'
}, { immediate: true })

watch(() => form.party_type, (pt, prev) => {
  if (prev && pt !== prev) {
    form.parent_id = null
    refreshParents()
  }
})

async function saveParty() {
  editError.value = ''
  saving.value = true
  try {
    await api(`/customers/${id.value}`, {
      method: 'PATCH',
      body: {
        name: form.name,
        party_type: form.party_type,
        parent_id: form.party_type === 'DISTRIBUTOR' ? null : form.parent_id,
        acquisition_source: form.acquisition_source || null,
        phone: form.phone || null,
        email: form.email || null,
        gstin: form.gstin || null,
        status: form.status
      }
    })
    await refresh()
  } catch (e: unknown) {
    editError.value = (e as { data?: { message?: string } })?.data?.message || 'Failed to save'
  } finally {
    saving.value = false
  }
}

const childType = ref('')
watch(c, (party) => {
  const allowed = party?.allowed_child_types || []
  if (allowed.length && !allowed.includes(childType.value)) {
    childType.value = allowed[0]
  }
}, { immediate: true })

function addChild() {
  if (!childType.value) return
  navigateTo(`/admin/customers/new?parent_id=${id.value}&party_type=${childType.value}`)
}

const portalForm = reactive({
  email: '',
  password: '',
  name: '',
  phone: ''
})
const portalError = ref('')
const portalLoading = ref(false)
const showPortalForm = ref(false)

watch(c, (party) => {
  if (!party) return
  portalForm.email = party.email || ''
  portalForm.name = party.name || ''
  portalForm.phone = party.phone || ''
  portalForm.password = ''
}, { immediate: true })

async function createPortalLogin() {
  portalError.value = ''
  portalLoading.value = true
  try {
    await api(`/customers/${id.value}/portal-login`, {
      method: 'POST',
      body: {
        email: portalForm.email,
        password: portalForm.password,
        name: portalForm.name || undefined,
        phone: portalForm.phone || undefined
      }
    })
    showPortalForm.value = false
    portalForm.password = ''
    await refresh()
  } catch (e: unknown) {
    portalError.value = (e as { data?: { message?: string } })?.data?.message || 'Failed'
  } finally {
    portalLoading.value = false
  }
}

async function unlinkPortalLogin() {
  if (!confirm('Unlink portal login from this party? The account will be disabled.')) return
  portalError.value = ''
  portalLoading.value = true
  try {
    await api(`/customers/${id.value}/portal-login`, { method: 'DELETE' })
    await refresh()
  } catch (e: unknown) {
    portalError.value = (e as { data?: { message?: string } })?.data?.message || 'Failed'
  } finally {
    portalLoading.value = false
  }
}

const canWrite = computed(() => auth.hasPermission('customers.write'))
</script>

<template>
  <AdminPage
    v-if="c"
    :title="c.name"
    :description="`${c.party_type}${c.acquisition_source ? ' · ' + c.acquisition_source : ''}`"
  >
    <template
      v-if="canWrite && (c.allowed_child_types || []).length"
      #actions
    >
      <div class="flex flex-wrap items-center gap-2">
        <USelect
          v-model="childType"
          :items="(c.allowed_child_types || []).map(t => ({ label: t.charAt(0) + t.slice(1).toLowerCase(), value: t }))"
          class="w-36"
        />
        <UButton @click="addChild">
          Add child
        </UButton>
      </div>
    </template>

    <p
      v-if="status === 'pending'"
      class="text-ink-muted"
    >
      Loading…
    </p>

    <section
      v-if="canWrite"
      class="max-w-lg space-y-3 border-b border-gold-300/60 pb-8"
    >
      <h2 class="font-display text-xl">
        Edit party
      </h2>
      <p class="text-sm text-ink-muted">
        Remap parent or change type without requiring the party to register.
      </p>
      <UFormField label="Name">
        <UInput
          v-model="form.name"
          required
          class="w-full"
        />
      </UFormField>
      <UFormField label="Party type">
        <USelect
          v-model="form.party_type"
          :items="[
            { label: 'Distributor', value: 'DISTRIBUTOR' },
            { label: 'Dealer', value: 'DEALER' },
            { label: 'Retailer', value: 'RETAILER' },
            { label: 'Customer', value: 'CUSTOMER' }
          ]"
          class="w-full"
        />
      </UFormField>
      <UFormField
        v-if="parentTypes.length"
        label="Parent"
      >
        <USelect
          v-model="form.parent_id"
          :items="parentSelectItems"
          class="w-full"
        />
      </UFormField>
      <p
        v-else
        class="text-sm text-ink-muted"
      >
        Distributors are top-level (no parent).
      </p>
      <UFormField label="Acquisition">
        <USelect
          v-model="form.acquisition_source"
          :items="[
            { label: '—', value: '' },
            { label: 'Walk-in', value: 'WALK_IN' },
            { label: 'Online', value: 'ONLINE' },
            { label: 'FB lead', value: 'FB_LEAD' },
            { label: 'Referral', value: 'REFERRAL' },
            { label: 'Phone', value: 'PHONE' },
            { label: 'Other', value: 'OTHER' }
          ]"
          class="w-full"
        />
      </UFormField>
      <UFormField label="Phone">
        <UInput
          v-model="form.phone"
          class="w-full"
        />
      </UFormField>
      <UFormField label="Email">
        <UInput
          v-model="form.email"
          type="email"
          class="w-full"
        />
      </UFormField>
      <UFormField label="GSTIN">
        <UInput
          v-model="form.gstin"
          class="w-full"
        />
      </UFormField>
      <UFormField label="Status">
        <USelect
          v-model="form.status"
          :items="[
            { label: 'Active', value: 'ACTIVE' },
            { label: 'Inactive', value: 'INACTIVE' }
          ]"
          class="w-full"
        />
      </UFormField>
      <p
        v-if="editError"
        class="text-sm text-red-700"
      >
        {{ editError }}
      </p>
      <UButton
        :loading="saving"
        @click="saveParty"
      >
        Save changes
      </UButton>
    </section>

    <dl
      v-else
      class="grid gap-3 text-sm sm:grid-cols-2"
    >
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
            v-if="c.parent"
            :to="`/admin/customers/${c.parent.id}`"
            class="text-gold-800 underline"
          >
            {{ c.parent.name }} ({{ c.parent.party_type }})
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
      Portal login
    </h2>
    <p class="mt-1 text-sm text-ink-muted">
      Optional. Most distributors and dealers are mapped here without self-registering.
    </p>
    <div
      v-if="c.portal_user"
      class="mt-3 space-y-2 text-sm"
    >
      <p>
        <span class="font-medium">{{ c.portal_user.name }}</span>
        · {{ c.portal_user.email }}
        · {{ c.portal_user.role }}
        · {{ c.portal_user.status }}
      </p>
      <UButton
        v-if="canWrite"
        color="neutral"
        variant="outline"
        :loading="portalLoading"
        @click="unlinkPortalLogin"
      >
        Unlink login
      </UButton>
    </div>
    <div
      v-else-if="canWrite"
      class="mt-3"
    >
      <UButton
        v-if="!showPortalForm"
        variant="outline"
        @click="showPortalForm = true"
      >
        Create portal login
      </UButton>
      <form
        v-else
        class="max-w-lg space-y-3"
        @submit.prevent="createPortalLogin"
      >
        <UFormField label="Login email">
          <UInput
            v-model="portalForm.email"
            type="email"
            required
            class="w-full"
          />
        </UFormField>
        <UFormField label="Password">
          <UInput
            v-model="portalForm.password"
            type="password"
            required
            minlength="8"
            class="w-full"
          />
        </UFormField>
        <UFormField label="Display name">
          <UInput
            v-model="portalForm.name"
            class="w-full"
          />
        </UFormField>
        <UFormField label="Phone">
          <UInput
            v-model="portalForm.phone"
            class="w-full"
          />
        </UFormField>
        <p
          v-if="portalError"
          class="text-sm text-red-700"
        >
          {{ portalError }}
        </p>
        <div class="flex gap-2">
          <UButton
            type="submit"
            :loading="portalLoading"
          >
            Create &amp; link
          </UButton>
          <UButton
            type="button"
            color="neutral"
            variant="ghost"
            @click="showPortalForm = false"
          >
            Cancel
          </UButton>
        </div>
      </form>
    </div>
    <p
      v-else
      class="mt-3 text-sm text-ink-muted"
    >
      No portal login linked.
    </p>
    <p
      v-if="portalError && c.portal_user"
      class="mt-2 text-sm text-red-700"
    >
      {{ portalError }}
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
        No children. Use Add child to attach a dealer, retailer, or customer.
      </li>
    </ul>
  </AdminPage>
</template>
