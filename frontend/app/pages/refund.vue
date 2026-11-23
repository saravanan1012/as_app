<script setup lang="ts">
const vendor = useVendorStore()
const lastUpdated = '23 November 2026'
const WHATSAPP_DISPLAY = '+91 70109 70849'
const WHATSAPP_URL = 'https://wa.me/917010970849'
const SUPPORT_EMAIL = 'premaagency18@gmail.com'

useSeoMeta({
  title: () => `Refund & Return Policy · ${vendor.brandName}`,
  description: () =>
    `Refund and return rules for ${vendor.brandName} orders — hygiene products, damaged or incorrect items, and how to contact support.`
})
</script>

<template>
  <div class="mx-auto max-w-3xl px-4 py-10 sm:px-6 sm:py-14">
    <div class="flex flex-wrap items-end justify-between gap-4">
      <div>
        <h1 class="font-display text-4xl text-ink">
          Refund &amp; Return Policy
        </h1>
        <p class="mt-2 text-sm text-ink-muted">
          Last updated: {{ lastUpdated }}
        </p>
      </div>
      <div class="flex flex-wrap gap-2">
        <UButton
          to="/terms"
          variant="outline"
          color="neutral"
          size="sm"
        >
          Terms
        </UButton>
        <UButton
          to="/contact"
          variant="outline"
          color="neutral"
          size="sm"
        >
          Contact
        </UButton>
      </div>
    </div>

    <div class="mt-10 space-y-8 text-sm leading-relaxed text-ink-muted">
      <section>
        <p>
          At {{ vendor.brandName }}, customer satisfaction is our priority.
          We are committed to providing quality products and a pleasant shopping experience.
        </p>
      </section>

      <section>
        <h2 class="font-display text-xl text-ink">
          1. Returns &amp; Exchanges
        </h2>
        <p class="mt-2">
          For hygiene and safety reasons, sanitary napkins
          <strong class="text-ink">cannot be returned or exchanged</strong>
          once the package has been opened or used.
        </p>
      </section>

      <section>
        <h2 class="font-display text-xl text-ink">
          2. Damaged or Incorrect Products
        </h2>
        <p class="mt-2">
          If you receive a damaged, defective, or incorrect product, please contact us within
          <strong class="text-ink">48 hours</strong>
          of delivery with your order details and clear photographs or an unboxing video.
        </p>
      </section>

      <section>
        <h2 class="font-display text-xl text-ink">
          3. Refund Eligibility
        </h2>
        <p class="mt-2">
          Refunds may be considered for verified cases of damaged, defective, incorrect, or missing products.
        </p>
      </section>

      <section>
        <h2 class="font-display text-xl text-ink">
          4. Refund Process
        </h2>
        <p class="mt-2">
          Once your complaint is reviewed and approved, the eligible refund will be processed to your original payment method
          or through another mutually agreed payment method.
        </p>
      </section>

      <section>
        <h2 class="font-display text-xl text-ink">
          5. Contact Us
        </h2>
        <p class="mt-2">
          For refund, return, or exchange-related queries, please contact our customer support team.
        </p>
        <ul class="mt-2 list-none space-y-1">
          <li>
            WhatsApp:
            <a
              :href="WHATSAPP_URL"
              class="text-gold-800 underline"
              target="_blank"
              rel="noopener noreferrer"
            >{{ WHATSAPP_DISPLAY }}</a>
          </li>
          <li>
            Email:
            <a
              :href="`mailto:${SUPPORT_EMAIL}`"
              class="text-gold-800 underline"
            >{{ SUPPORT_EMAIL }}</a>
          </li>
          <li>
            Or
            <NuxtLink
              to="/contact"
              class="text-gold-800 underline"
            >Contact</NuxtLink>
            /
            <NuxtLink
              to="/store/orders"
              class="text-gold-800 underline"
            >My orders</NuxtLink>
            (when signed in).
          </li>
        </ul>
        <p class="mt-4 text-ink">
          {{ vendor.brandName }} — Your Comfort and Trust Matter to Us!
        </p>
        <p class="mt-1 italic text-ink-muted">
          We're just a message away!
        </p>
      </section>

      <section>
        <h2 class="font-display text-xl text-ink">
          Related policies
        </h2>
        <p class="mt-2">
          <NuxtLink
            to="/terms"
            class="text-gold-800 underline"
          >Terms &amp; Conditions</NuxtLink>
          ·
          <NuxtLink
            to="/privacy"
            class="text-gold-800 underline"
          >Privacy Policy</NuxtLink>.
        </p>
      </section>
    </div>
  </div>
</template>
