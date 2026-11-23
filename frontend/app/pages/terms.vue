<script setup lang="ts">
const vendor = useVendorStore()
const lastUpdated = '23 November 2026'
const WHATSAPP_DISPLAY = '+91 70109 70849'
const WHATSAPP_URL = 'https://wa.me/917010970849'
const SUPPORT_EMAIL = 'premaagency18@gmail.com'

useSeoMeta({
  title: () => `Terms & Conditions · ${vendor.brandName}`,
  description: () =>
    `Terms & Conditions for visiting ${vendor.brandName} and purchasing our products online.`
})
</script>

<template>
  <div class="mx-auto max-w-3xl px-4 py-10 sm:px-6 sm:py-14">
    <div class="flex flex-wrap items-end justify-between gap-4">
      <div>
        <h1 class="font-display text-4xl text-ink">
          Terms &amp; Conditions
        </h1>
        <p class="mt-2 text-sm text-ink-muted">
          Last updated: {{ lastUpdated }}
        </p>
      </div>
      <div class="flex flex-wrap gap-2">
        <UButton
          to="/privacy"
          variant="outline"
          color="neutral"
          size="sm"
        >
          Privacy
        </UButton>
        <UButton
          to="/refund"
          variant="outline"
          color="neutral"
          size="sm"
        >
          Refunds
        </UButton>
      </div>
    </div>

    <div class="mt-10 space-y-8 text-sm leading-relaxed text-ink-muted">
      <section>
        <p>
          Welcome to {{ vendor.brandName }}! By visiting our website or purchasing our products, you agree to the following Terms &amp; Conditions.
        </p>
      </section>

      <section>
        <h2 class="font-display text-xl text-ink">
          1. Product Information
        </h2>
        <p class="mt-2">
          We strive to provide accurate product descriptions, images, sizes, and prices.
          Minor variations in product appearance or packaging may occur.
        </p>
      </section>

      <section>
        <h2 class="font-display text-xl text-ink">
          2. Orders &amp; Payments
        </h2>
        <p class="mt-2">
          All orders are subject to product availability and confirmation.
          Customers must provide accurate contact, billing, and delivery information.
          Payments must be completed through the available payment methods.
        </p>
      </section>

      <section>
        <h2 class="font-display text-xl text-ink">
          3. Pricing &amp; Offers
        </h2>
        <p class="mt-2">
          Prices, discounts, and promotional offers are subject to change without prior notice.
          The confirmed order price will apply to your purchase.
        </p>
      </section>

      <section>
        <h2 class="font-display text-xl text-ink">
          4. Shipping &amp; Delivery
        </h2>
        <p class="mt-2">
          We aim to deliver orders within the estimated delivery period.
          Delivery times may vary depending on location, courier services, and unforeseen circumstances.
        </p>
      </section>

      <section>
        <h2 class="font-display text-xl text-ink">
          5. Order Cancellation
        </h2>
        <p class="mt-2">
          Orders can be cancelled before dispatch.
          Once an order has been shipped, cancellation may not be possible.
        </p>
      </section>

      <section>
        <h2 class="font-display text-xl text-ink">
          6. Returns &amp; Refunds
        </h2>
        <p class="mt-2">
          Due to hygiene and safety reasons, opened or used sanitary napkin packages cannot be returned or exchanged.
          Damaged, defective, incorrect, or missing products will be handled according to our
          <NuxtLink
            to="/refund"
            class="text-gold-800 underline"
          >Refund &amp; Return Policy</NuxtLink>
          and applicable consumer laws.
        </p>
      </section>

      <section>
        <h2 class="font-display text-xl text-ink">
          7. Product Usage
        </h2>
        <p class="mt-2">
          Please follow the product instructions and recommended usage guidelines.
          Discontinue use if irritation or discomfort occurs.
        </p>
      </section>

      <section>
        <h2 class="font-display text-xl text-ink">
          8. Privacy Policy
        </h2>
        <p class="mt-2">
          We respect your privacy. Your personal information will be used for order processing, delivery, and customer support in accordance with our
          <NuxtLink
            to="/privacy"
            class="text-gold-800 underline"
          >Privacy Policy</NuxtLink>.
        </p>
      </section>

      <section>
        <h2 class="font-display text-xl text-ink">
          9. Limitation of Liability
        </h2>
        <p class="mt-2">
          We are not responsible for delays or interruptions caused by circumstances beyond our reasonable control.
          Nothing in these terms limits your statutory consumer rights.
        </p>
      </section>

      <section>
        <h2 class="font-display text-xl text-ink">
          10. Changes to Terms
        </h2>
        <p class="mt-2">
          {{ vendor.brandName }} reserves the right to update these Terms &amp; Conditions when necessary.
          Changes will be published on our website. The “Last updated” date above will change when we do.
        </p>
      </section>

      <section>
        <h2 class="font-display text-xl text-ink">
          11. Contact Information
        </h2>
        <ul class="mt-2 list-none space-y-1">
          <li>
            Brand: <strong class="text-ink">{{ vendor.brandName }}</strong>
          </li>
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
            Or use our
            <NuxtLink
              to="/contact"
              class="text-gold-800 underline"
            >Contact</NuxtLink>
            page.
          </li>
        </ul>
        <p class="mt-4 text-ink">
          Thank you for choosing {{ vendor.brandName }}!
        </p>
        <p class="mt-1 italic text-ink-muted">
          Pure Care. Natural Comfort. Confident You.
        </p>
      </section>
    </div>
  </div>
</template>
