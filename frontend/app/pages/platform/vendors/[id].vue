<script setup lang="ts">
definePageMeta({ layout: 'platform', middleware: ['platform'] })

const route = useRoute()
const { api } = useApi()
const adminCtx = useAdminContextStore()
const id = computed(() => Number(route.params.id))

const { data, refresh } = await useAdminAsyncData(() => `vendor-${id.value}`, () =>
  api<{
    id: number
    name: string
    slug: string
    status: string
    store_enabled?: boolean
    settings: {
      features?: { store_enabled?: boolean }
      branding?: {
        store_name?: string
        company_tagline?: string
        company_blurb?: string
        theme_id?: string
        primary?: string
      }
    }
  }>(`/platform/vendors/${id.value}`)
)

const vendor = computed(() => data.value?.data)
const branding = reactive({
  store_name: '',
  company_tagline: '',
  company_blurb: '',
  theme_id: 'matte_gold',
  primary: '#D4AF7C'
})

watch(vendor, (v) => {
  if (!v) return
  const b = v.settings?.branding || {}
  branding.store_name = b.store_name || v.name
  branding.company_tagline = b.company_tagline || ''
  branding.company_blurb = b.company_blurb || ''
  branding.theme_id = b.theme_id || 'matte_gold'
  branding.primary = b.primary || '#D4AF7C'
}, { immediate: true })

const storeOn = computed(() => !!(vendor.value?.store_enabled ?? vendor.value?.settings?.features?.store_enabled))

async function toggleStore(val: boolean) {
  await api(`/platform/vendors/${id.value}/store`, {
    method: 'PATCH',
    body: { store_enabled: val }
  })
  await refresh()
}

async function saveBranding() {
  await api(`/platform/vendors/${id.value}/settings`, {
    method: 'PATCH',
    body: { branding }
  })
  await refresh()
}

function openAdmin() {
  adminCtx.setVendorId(id.value)
  navigateTo('/admin')
}
</script>

<template>
  <div
    v-if="vendor"
    class="max-w-2xl space-y-8"
  >
    <div class="flex flex-wrap items-start justify-between gap-3">
      <div>
        <h1 class="font-display text-3xl">
          {{ vendor.name }}
        </h1>
        <p class="text-ink-muted">
          {{ vendor.slug }} · {{ vendor.status }}
        </p>
      </div>
      <UButton @click="openAdmin">
        Open vendor admin
      </UButton>
    </div>

    <section class="border-y border-gold-300/70 py-5">
      <div class="flex items-center justify-between gap-4">
        <div>
          <h2 class="font-display text-xl">
            Store
          </h2>
          <p class="text-sm text-ink-muted">
            Enable ecommerce routes and Store APIs for this vendor.
          </p>
        </div>
        <USwitch
          :model-value="storeOn"
          @update:model-value="toggleStore"
        />
      </div>
    </section>

    <section class="space-y-4">
      <h2 class="font-display text-xl">
        Branding
      </h2>
      <UFormField label="Store name">
        <UInput
          v-model="branding.store_name"
          class="w-full"
          size="lg"
        />
      </UFormField>
      <UFormField label="Tagline">
        <UInput
          v-model="branding.company_tagline"
          class="w-full"
          size="lg"
        />
      </UFormField>
      <UFormField label="Blurb">
        <UTextarea
          v-model="branding.company_blurb"
          class="w-full"
          :rows="3"
        />
      </UFormField>
      <UFormField label="Theme">
        <USelect
          v-model="branding.theme_id"
          :items="[
            { label: 'Matte Gold', value: 'matte_gold' },
            { label: 'Rose Gold', value: 'rose_gold' },
            { label: 'Deep Gold', value: 'deep_gold' },
            { label: 'Vibrant Gold', value: 'vibrant_gold' }
          ]"
          class="w-full"
          size="lg"
        />
      </UFormField>
      <UButton @click="saveBranding">
        Save branding
      </UButton>
    </section>
  </div>
</template>
