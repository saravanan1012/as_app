<script setup lang="ts">
const vendor = useVendorStore()

const PHONE = '7010970849'
const PHONE_E164 = `91${PHONE}`
const WHATSAPP_URL = `https://wa.me/${PHONE_E164}`
const TEL_URL = `tel:+${PHONE_E164}`

const ADDRESS_LINES = [
  'Prema Agency',
  '1st Floor, 55/20, Kuppanna Chetti Street',
  'Pichanoor, Gudiyatham',
  'Tamil Nadu 632602'
]

const MAP_LAT = 12.9500169
const MAP_LNG = 78.8661846
const MAP_PLACE_URL
  = 'https://www.google.com/maps/place/AS+Sanitary+Napkins+(+cotton+and+Organic)/@12.948069,78.8592131,14.35z/data=!4m6!3m5!1s0x3bad6d1d47b13bd3:0x226f9b6b5dac84fa!8m2!3d12.9500169!4d78.8661846!16s%2Fg%2F11z_pk7fhz?entry=ttu'
const MAP_EMBED_SRC = `https://maps.google.com/maps?q=${MAP_LAT},${MAP_LNG}&z=15&hl=en&output=embed`

const form = reactive({
  name: '',
  email: '',
  phone: '',
  subject: '',
  message: ''
})
const sentHint = ref('')
const error = ref('')

function buildMessageBody() {
  return [
    `Name: ${form.name.trim()}`,
    `Email: ${form.email.trim() || '—'}`,
    `Phone: ${form.phone.trim() || '—'}`,
    `Subject: ${form.subject.trim() || 'Enquiry'}`,
    '',
    form.message.trim()
  ].join('\n')
}

function submitWhatsApp() {
  error.value = ''
  sentHint.value = ''
  if (!form.name.trim() || !form.message.trim()) {
    error.value = 'Please enter your name and message.'
    return
  }
  const text = encodeURIComponent(buildMessageBody())
  window.open(`${WHATSAPP_URL}?text=${text}`, '_blank', 'noopener,noreferrer')
  sentHint.value = 'WhatsApp opened with your message — send it to complete.'
}

function submitMailto() {
  error.value = ''
  sentHint.value = ''
  if (!form.name.trim() || !form.message.trim()) {
    error.value = 'Please enter your name and message.'
    return
  }
  const subject = encodeURIComponent(form.subject.trim() || `Enquiry — ${vendor.brandName}`)
  const body = encodeURIComponent(buildMessageBody())
  window.location.href = `mailto:?subject=${subject}&body=${body}`
  sentHint.value = 'Your email app should open with the message ready to send.'
}

useSeoMeta({
  title: () => `Contact · ${vendor.brandName}`,
  description: () =>
    `Contact Prema Agency / ${vendor.brandName} in Gudiyatham — call, WhatsApp, or send an enquiry.`
})
</script>

<template>
  <div class="mx-auto max-w-5xl px-4 py-14 sm:px-6">
    <h1 class="font-display text-4xl text-ink">
      Contact us
    </h1>
    <p class="mt-3 max-w-xl text-ink-muted">
      Reach {{ vendor.brandName }} for product questions, orders, or wholesale. Visit us in Gudiyatham or message below.
    </p>

    <div class="mt-12 grid gap-12 lg:grid-cols-2 lg:gap-16">
      <div class="space-y-8">
        <div>
          <p class="text-sm uppercase tracking-[0.2em] text-gold-800">
            Address
          </p>
          <p class="font-display mt-2 text-2xl text-ink">
            Prema Agency
          </p>
          <address class="mt-2 not-italic leading-relaxed text-ink-muted">
            <template
              v-for="(line, i) in ADDRESS_LINES.slice(1)"
              :key="i"
            >
              {{ line }}<br v-if="i < ADDRESS_LINES.length - 2">
            </template>
          </address>
        </div>

        <div>
          <p class="text-sm uppercase tracking-[0.2em] text-gold-800">
            Call / WhatsApp
          </p>
          <p class="mt-2 text-lg text-ink">
            <a
              :href="TEL_URL"
              class="font-medium text-gold-800 hover:underline"
            >{{ PHONE }}</a>
          </p>
          <div class="mt-4 flex flex-wrap gap-3">
            <UButton
              :to="TEL_URL"
              size="lg"
              color="primary"
            >
              Call
            </UButton>
            <UButton
              :to="WHATSAPP_URL"
              target="_blank"
              external
              size="lg"
              variant="outline"
              color="neutral"
            >
              WhatsApp
            </UButton>
          </div>
        </div>

        <div>
          <p class="text-sm uppercase tracking-[0.2em] text-gold-800">
            Scan to connect
          </p>
          <p class="mt-2 text-sm text-ink-muted">
            Scan with your phone camera for WhatsApp or AS Signature.
          </p>
          <div class="mt-4 grid grid-cols-2 gap-4 max-w-md">
            <a
              :href="WHATSAPP_URL"
              target="_blank"
              rel="noopener noreferrer"
              class="flex flex-col items-center gap-2 rounded-lg border border-gold-300/50 bg-gold-100/30 p-3 transition hover:border-gold-600"
            >
              <img
                src="/images/whatsapp-qr.png"
                alt="WhatsApp QR code"
                width="160"
                height="160"
                class="h-36 w-36 object-contain sm:h-40 sm:w-40"
              >
              <span class="text-sm font-medium text-ink">WhatsApp</span>
            </a>
            <div class="flex flex-col items-center gap-2 rounded-lg border border-gold-300/50 bg-gold-100/30 p-3">
              <img
                src="/images/assignature-qr.png"
                alt="AS Signature QR code"
                width="160"
                height="160"
                class="h-36 w-36 object-contain sm:h-40 sm:w-40"
              >
              <span class="text-sm font-medium text-ink">AS Signature</span>
            </div>
          </div>
        </div>

        <div v-if="vendor.storeEnabled">
          <p class="text-sm uppercase tracking-[0.2em] text-gold-800">
            Online Store
          </p>
          <p class="mt-2 text-ink-muted">
            Prefer to order online?
          </p>
          <UButton
            to="/store"
            class="mt-3"
            variant="ghost"
            color="primary"
          >
            Shop the Store
          </UButton>
        </div>
      </div>

      <div>
        <p class="text-sm uppercase tracking-[0.2em] text-gold-800">
          Send a message
        </p>
        <h2 class="font-display mt-2 text-2xl text-ink">
          Enquiry form
        </h2>
        <p class="mt-2 text-sm text-ink-muted">
          Fill in your details, then send via WhatsApp or your email app.
        </p>

        <form
          class="mt-6 space-y-4"
          @submit.prevent="submitWhatsApp"
        >
          <UFormField label="Name" required>
            <UInput
              v-model="form.name"
              size="lg"
              class="w-full"
              autocomplete="name"
            />
          </UFormField>
          <UFormField label="Email">
            <UInput
              v-model="form.email"
              type="email"
              size="lg"
              class="w-full"
              autocomplete="email"
            />
          </UFormField>
          <UFormField label="Phone">
            <UInput
              v-model="form.phone"
              type="tel"
              size="lg"
              class="w-full"
              autocomplete="tel"
            />
          </UFormField>
          <UFormField label="Subject">
            <UInput
              v-model="form.subject"
              size="lg"
              class="w-full"
              placeholder="Orders, wholesale, product question…"
            />
          </UFormField>
          <UFormField label="Message" required>
            <UTextarea
              v-model="form.message"
              :rows="5"
              class="w-full"
              autoresize
            />
          </UFormField>

          <p
            v-if="error"
            class="text-sm text-red-700"
          >
            {{ error }}
          </p>
          <p
            v-if="sentHint"
            class="text-sm text-ink"
          >
            {{ sentHint }}
          </p>

          <div class="flex flex-wrap gap-3">
            <UButton
              type="submit"
              size="xl"
            >
              Send on WhatsApp
            </UButton>
            <UButton
              type="button"
              size="xl"
              variant="outline"
              color="neutral"
              @click="submitMailto"
            >
              Open in Email
            </UButton>
          </div>
        </form>
      </div>
    </div>

    <section class="mt-16 border-t border-gold-300/50 pt-12">
      <div class="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p class="text-sm uppercase tracking-[0.2em] text-gold-800">
            Find us
          </p>
          <h2 class="font-display mt-2 text-2xl text-ink">
            {{ vendor.brandName }} — Gudiyatham
          </h2>
          <p class="mt-1 text-sm text-ink-muted">
            Cotton &amp; organic · map location
          </p>
        </div>
        <UButton
          :to="MAP_PLACE_URL"
          target="_blank"
          external
          variant="outline"
          color="neutral"
          size="sm"
        >
          Open in Google Maps
        </UButton>
      </div>
      <div class="mt-6 overflow-hidden border border-gold-300/50 bg-gold-100/40">
        <iframe
          :title="`${vendor.brandName} on Google Maps`"
          :src="MAP_EMBED_SRC"
          class="h-72 w-full border-0 sm:h-96"
          loading="lazy"
          referrerpolicy="no-referrer-when-downgrade"
          allowfullscreen
        />
      </div>
    </section>
  </div>
</template>
