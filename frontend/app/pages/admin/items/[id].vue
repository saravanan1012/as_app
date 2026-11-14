<script setup lang="ts">
import { mediaKind } from '~/utils/mediaKind'

definePageMeta({ layout: 'admin', middleware: ['admin'] })

const route = useRoute()
const auth = useAuthStore()
const { api } = useApi()
const id = computed(() => Number(route.params.id))
const canWrite = computed(() => auth.hasPermission('catalog.items.write'))

const { data, refresh } = await useAdminAsyncData(() => `item-${id.value}`, () =>
  api<Record<string, any>>(`/items/${id.value}`)
)
const item = computed(() => data.value?.data)

type MediaRow = {
  id: number
  path: string
  sort_order: number
  is_primary: boolean
  media_type?: 'image' | 'video'
}

const { data: mediaRes, refresh: refreshMedia } = await useAdminAsyncData(
  () => `item-media-${id.value}`,
  () => api<{ data: MediaRow[] }>(`/uploads/items/${id.value}/images`)
)
const mediaItems = computed(() => mediaRes.value?.data?.data || [])

const form = reactive({
  name: '',
  sale_price: 0,
  cost_price: 0,
  is_online_sale: false,
  is_sellable: true,
  sale_price_includes_gst: true,
  tax_category_id: null as number | null,
  status: 'ACTIVE',
  description: ''
})
const error = ref('')
const mediaError = ref('')
const saving = ref(false)
const priceSaving = ref(false)
const uploading = ref(false)
const mediaBusyId = ref<number | null>(null)
const fileInput = ref<HTMLInputElement | null>(null)
const previewOpen = ref(false)
const previewIndex = ref(0)

const previewItem = computed(() => mediaItems.value[previewIndex.value] || null)

function kindOf(m: MediaRow) {
  return m.media_type || mediaKind(m.path)
}

function openPreview(index: number) {
  previewIndex.value = index
  previewOpen.value = true
}

function previewPrev() {
  if (!mediaItems.value.length) return
  previewIndex.value = (previewIndex.value - 1 + mediaItems.value.length) % mediaItems.value.length
}

function previewNext() {
  if (!mediaItems.value.length) return
  previewIndex.value = (previewIndex.value + 1) % mediaItems.value.length
}

async function onFilesSelected(ev: Event) {
  const input = ev.target as HTMLInputElement
  const files = Array.from(input.files || [])
  if (!files.length) return
  mediaError.value = ''
  uploading.value = true
  try {
    for (const file of files) {
      const fd = new FormData()
      fd.append('file', file)
      await api(`/uploads/items/${id.value}/images`, { method: 'POST', body: fd })
    }
    await Promise.all([refreshMedia(), refresh()])
  } catch (e: unknown) {
    mediaError.value
      = (e as { data?: { message?: string } })?.data?.message || 'Upload failed'
  } finally {
    uploading.value = false
    input.value = ''
  }
}

async function setPrimary(m: MediaRow) {
  if (kindOf(m) === 'video') {
    mediaError.value = 'Only images can be primary'
    return
  }
  mediaError.value = ''
  mediaBusyId.value = m.id
  try {
    await api(`/uploads/items/${id.value}/images/${m.id}?is_primary=true`, { method: 'PATCH' })
    await Promise.all([refreshMedia(), refresh()])
  } catch (e: unknown) {
    mediaError.value
      = (e as { data?: { message?: string } })?.data?.message || 'Could not set primary'
  } finally {
    mediaBusyId.value = null
  }
}

async function removeMedia(m: MediaRow) {
  if (!confirm('Remove this media file?')) return
  mediaError.value = ''
  mediaBusyId.value = m.id
  try {
    await api(`/uploads/items/${id.value}/images/${m.id}`, { method: 'DELETE' })
    if (previewOpen.value && previewItem.value?.id === m.id) {
      previewOpen.value = false
    }
    await Promise.all([refreshMedia(), refresh()])
  } catch (e: unknown) {
    mediaError.value
      = (e as { data?: { message?: string } })?.data?.message || 'Delete failed'
  } finally {
    mediaBusyId.value = null
  }
}

const { data: taxCatsRes } = await useAdminAsyncData('item-tax-categories', () =>
  api<Array<Record<string, any>>>('/tax-categories')
)
const taxOptions = computed(() => {
  const rows = Array.isArray(taxCatsRes.value?.data) ? taxCatsRes.value!.data : []
  return [
    { label: 'None (0%)', value: null as number | null },
    ...rows.map((t: any) => ({
      label: `${t.code} — ${t.gst_rate}%`,
      value: t.id as number
    }))
  ]
})

type PriceRow = { party_type: string, mode: string, value: number }
const priceRows = reactive<PriceRow[]>([
  { party_type: 'DISTRIBUTOR', mode: 'PERCENT_OFF', value: 0 },
  { party_type: 'DEALER', mode: 'PERCENT_OFF', value: 0 },
  { party_type: 'RETAILER', mode: 'PERCENT_OFF', value: 0 }
])

const { data: rulesRes, refresh: refreshRules } = await useAdminAsyncData(
  () => `price-rules-${id.value}`,
  () => api<{ data: Array<Record<string, any>> }>(`/party-price-rules?item_id=${id.value}`)
)

watch(item, (i) => {
  if (!i) return
  form.name = i.name
  form.sale_price = Number(i.sale_price)
  form.cost_price = Number(i.cost_price)
  form.is_online_sale = !!i.is_online_sale
  form.is_sellable = !!i.is_sellable
  form.sale_price_includes_gst = i.sale_price_includes_gst !== false
  form.tax_category_id = i.tax_category_id ?? null
  form.status = i.status
  form.description = i.description || ''
}, { immediate: true })

watch(rulesRes, (r) => {
  const rows = r?.data?.data || []
  for (const pr of priceRows) {
    const found = rows.find((x: any) => x.party_type === pr.party_type)
    if (found) {
      pr.mode = found.mode
      pr.value = Number(found.value)
    }
  }
}, { immediate: true })

async function save() {
  error.value = ''
  saving.value = true
  try {
    await api(`/items/${id.value}`, { method: 'PATCH', body: { ...form } })
    await refresh()
  } catch (e: unknown) {
    error.value = (e as { data?: { message?: string } })?.data?.message || 'Failed'
  } finally {
    saving.value = false
  }
}

async function savePrices() {
  priceSaving.value = true
  error.value = ''
  try {
    await api('/party-price-rules/bulk', {
      method: 'PUT',
      body: {
        item_id: id.value,
        rules: priceRows.map(r => ({
          item_id: id.value,
          party_type: r.party_type,
          mode: r.mode,
          value: r.value,
          status: 'ACTIVE'
        }))
      }
    })
    await refreshRules()
  } catch (e: unknown) {
    error.value = (e as { data?: { message?: string } })?.data?.message || 'Price save failed'
  } finally {
    priceSaving.value = false
  }
}
</script>

<template>
  <AdminPage
    v-if="item"
    :title="item.name"
    :description="item.code"
  >
    <form
      v-if="canWrite"
      class="max-w-lg space-y-4"
      @submit.prevent="save"
    >
      <UFormField label="Name">
        <UInput
          v-model="form.name"
          class="w-full"
          required
        />
      </UFormField>
      <UFormField label="Description">
        <UTextarea
          v-model="form.description"
          class="w-full"
        />
      </UFormField>
      <div class="grid grid-cols-2 gap-3">
        <UFormField label="Sale price">
          <UInput
            v-model.number="form.sale_price"
            type="number"
            step="0.01"
            class="w-full"
          />
        </UFormField>
        <UFormField label="Cost">
          <UInput
            v-model.number="form.cost_price"
            type="number"
            step="0.01"
            class="w-full"
          />
        </UFormField>
      </div>
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
      <UFormField label="Tax category (GST %)">
        <USelect
          v-model="form.tax_category_id"
          :items="taxOptions"
          class="w-full"
        />
      </UFormField>
      <div class="flex flex-wrap gap-4 text-sm">
        <label class="flex items-center gap-2">
          <input
            v-model="form.is_sellable"
            type="checkbox"
          >
          Sellable
        </label>
        <label class="flex items-center gap-2">
          <input
            v-model="form.is_online_sale"
            type="checkbox"
          >
          Online (Store)
        </label>
        <label class="flex items-center gap-2">
          <input
            v-model="form.sale_price_includes_gst"
            type="checkbox"
          >
          Price includes GST
        </label>
      </div>
      <p
        v-if="error"
        class="text-sm text-red-700"
      >
        {{ error }}
      </p>
      <UButton
        type="submit"
        :loading="saving"
      >
        Save
      </UButton>
    </form>

    <section class="mt-10 max-w-3xl space-y-4">
      <div class="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h2 class="font-display text-xl">
            Media
          </h2>
          <p class="text-sm text-ink-muted">
            Images (jpg/png/webp/gif, max 5MB) and videos (mp4/webm/mov, max 50MB). Primary image is used in listings.
          </p>
        </div>
        <div
          v-if="canWrite"
          class="flex flex-wrap items-center gap-2"
        >
          <input
            ref="fileInput"
            type="file"
            class="hidden"
            accept="image/jpeg,image/png,image/webp,image/gif,video/mp4,video/webm,video/quicktime,.jpg,.jpeg,.png,.webp,.gif,.mp4,.webm,.mov"
            multiple
            @change="onFilesSelected"
          >
          <UButton
            type="button"
            :loading="uploading"
            @click="fileInput?.click()"
          >
            Upload
          </UButton>
        </div>
      </div>

      <p
        v-if="mediaError"
        class="text-sm text-red-700"
      >
        {{ mediaError }}
      </p>

      <p
        v-if="!mediaItems.length"
        class="text-sm text-ink-muted"
      >
        No images or videos yet.
      </p>

      <div
        v-else
        class="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4"
      >
        <div
          v-for="(m, idx) in mediaItems"
          :key="m.id"
          class="group relative aspect-square overflow-hidden border border-gold-300/60 bg-gold-100/40"
        >
          <button
            type="button"
            class="absolute inset-0 z-[1] block h-full w-full cursor-zoom-in"
            :aria-label="`View ${kindOf(m)}`"
            @click="openPreview(idx)"
          />
          <video
            v-if="kindOf(m) === 'video'"
            :src="m.path"
            class="h-full w-full object-cover"
            muted
            playsinline
            preload="metadata"
          />
          <img
            v-else
            :src="m.path"
            :alt="`${item.name} media`"
            class="h-full w-full object-cover"
          >
          <div class="pointer-events-none absolute inset-x-0 top-0 z-[2] flex justify-between gap-1 p-1.5">
            <span
              v-if="m.is_primary"
              class="bg-gold-800 px-1.5 py-0.5 text-[10px] font-medium uppercase tracking-wide text-white"
            >
              Primary
            </span>
            <span
              v-if="kindOf(m) === 'video'"
              class="ml-auto bg-ink/70 px-1.5 py-0.5 text-[10px] font-medium uppercase tracking-wide text-white"
            >
              Video
            </span>
          </div>
          <div
            v-if="canWrite"
            class="absolute inset-x-0 bottom-0 z-[2] flex gap-1 p-1.5 opacity-100 sm:opacity-0 sm:transition sm:group-hover:opacity-100"
          >
            <UButton
              v-if="kindOf(m) === 'image' && !m.is_primary"
              size="xs"
              variant="soft"
              color="neutral"
              class="pointer-events-auto"
              :loading="mediaBusyId === m.id"
              @click.stop="setPrimary(m)"
            >
              Primary
            </UButton>
            <UButton
              size="xs"
              variant="soft"
              color="error"
              class="pointer-events-auto ml-auto"
              :loading="mediaBusyId === m.id"
              @click.stop="removeMedia(m)"
            >
              Remove
            </UButton>
          </div>
        </div>
      </div>
    </section>

    <UModal
      v-model:open="previewOpen"
      :title="previewItem ? (kindOf(previewItem) === 'video' ? 'Video' : 'Image') : 'Media'"
      :description="item.name"
      class="max-w-3xl"
    >
      <template #body>
        <div
          v-if="previewItem"
          class="space-y-3"
        >
          <div class="relative aspect-video overflow-hidden bg-ink/5">
            <video
              v-if="kindOf(previewItem) === 'video'"
              :key="previewItem.path"
              :src="previewItem.path"
              class="h-full w-full object-contain"
              controls
              playsinline
              autoplay
            />
            <img
              v-else
              :src="previewItem.path"
              :alt="item.name"
              class="h-full w-full object-contain"
            >
          </div>
          <div
            v-if="mediaItems.length > 1"
            class="flex items-center justify-between gap-2"
          >
            <UButton
              variant="outline"
              color="neutral"
              @click="previewPrev"
            >
              Previous
            </UButton>
            <p class="text-sm text-ink-muted">
              {{ previewIndex + 1 }} / {{ mediaItems.length }}
            </p>
            <UButton
              variant="outline"
              color="neutral"
              @click="previewNext"
            >
              Next
            </UButton>
          </div>
        </div>
      </template>
    </UModal>

    <section
      v-if="canWrite"
      class="mt-10 max-w-xl space-y-3"
    >
      <h2 class="font-display text-xl">
        Trade prices
      </h2>
      <p class="text-sm text-ink-muted">
        Percentage off MSRP, fixed off, or fixed price per party type.
      </p>
      <div
        v-for="row in priceRows"
        :key="row.party_type"
        class="grid grid-cols-[7rem_1fr_6rem] items-end gap-2"
      >
        <p class="pb-2 text-sm font-medium">
          {{ row.party_type }}
        </p>
        <USelect
          v-model="row.mode"
          :items="[
            { label: '% off MSRP', value: 'PERCENT_OFF' },
            { label: 'Fixed off', value: 'FIXED_OFF' },
            { label: 'Fixed price', value: 'FIXED_PRICE' }
          ]"
          class="w-full"
        />
        <UInput
          v-model.number="row.value"
          type="number"
          step="0.01"
          class="w-full"
        />
      </div>
      <UButton
        :loading="priceSaving"
        variant="outline"
        @click="savePrices"
      >
        Save trade prices
      </UButton>
    </section>

    <dl
      v-if="!canWrite"
      class="mt-6 grid gap-3 text-sm sm:grid-cols-2"
    >
      <div>
        <dt class="text-ink-muted">
          Sale
        </dt>
        <dd>₹{{ Number(item.sale_price).toFixed(2) }}</dd>
      </div>
      <div>
        <dt class="text-ink-muted">
          Status
        </dt>
        <dd>{{ item.status }}</dd>
      </div>
      <div>
        <dt class="text-ink-muted">
          Online
        </dt>
        <dd>{{ item.is_online_sale ? 'Yes' : 'No' }}</dd>
      </div>
    </dl>
  </AdminPage>
</template>
