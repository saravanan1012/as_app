<script setup lang="ts">
const vendor = useVendorStore()
const lastUpdated = '31 October 2026'

useSeoMeta({
  title: () => `Terms of Service · ${vendor.brandName}`,
  description: () =>
    `Terms for using ${vendor.brandName} website and Online Store for sanitary napkins and related products.`
})
</script>

<template>
  <div class="mx-auto max-w-3xl px-4 py-10 sm:px-6 sm:py-14">
    <div class="flex flex-wrap items-end justify-between gap-4">
      <div>
        <h1 class="font-display text-4xl text-ink">
          Terms of Service
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
        <h2 class="font-display text-xl text-ink">
          1. Acceptance
        </h2>
        <p class="mt-2">
          By accessing {{ vendor.brandName }} (the “Service”), including our product pages and Online Store, you agree to these Terms.
          If you do not agree, do not use the Service.
        </p>
      </section>

      <section>
        <h2 class="font-display text-xl text-ink">
          2. What we offer
        </h2>
        <p class="mt-2">
          We sell personal care products—primarily organic sanitary napkins in sizes such as M, L, XL, XXL, and XXXL—and may list related essentials.
          Product details, images, and prices on the site are for information; minor pack or artwork differences may occur.
          The Online Store (cart, checkout, orders) is available when enabled for this storefront.
        </p>
      </section>

      <section>
        <h2 class="font-display text-xl text-ink">
          3. Accounts
        </h2>
        <p class="mt-2">
          You must provide accurate registration and shipping details. You are responsible for keeping login credentials confidential
          and for activity under your account. We may suspend accounts that abuse the Service or violate these Terms.
        </p>
      </section>

      <section>
        <h2 class="font-display text-xl text-ink">
          4. Orders, pricing &amp; payment
        </h2>
        <ul class="mt-2 list-disc space-y-1 pl-5">
          <li>Prices are shown in INR and may include applicable taxes as indicated at checkout</li>
          <li>Payment options may include Cash on Delivery (COD) and prepaid checkout via Razorpay (UPI, cards, and other methods Razorpay supports)</li>
          <li>Placing an order is an offer to buy; we may cancel or refuse orders for stock, pricing error, fraud risk, or delivery constraints</li>
          <li>Stock is reserved or deducted according to the payment method; prepaid orders are confirmed after successful payment verification</li>
        </ul>
      </section>

      <section>
        <h2 class="font-display text-xl text-ink">
          5. Shipping &amp; delivery
        </h2>
        <p class="mt-2">
          Shipping charges (if any) are calculated at checkout. Delivery timelines are estimates and depend on courier and destination.
          Risk of loss passes according to our fulfilment process and applicable law once handed to the courier, unless we state otherwise.
        </p>
      </section>

      <section>
        <h2 class="font-display text-xl text-ink">
          6. Acceptable use
        </h2>
        <p class="mt-2">
          You may not misuse the store (fraudulent payments, scraping, interfering with systems, or reselling in violation of applicable law).
          Product reviews must be honest and not abusive.
        </p>
      </section>

      <section>
        <h2 class="font-display text-xl text-ink">
          7. Returns &amp; refunds
        </h2>
        <p class="mt-2">
          Hygiene products have special handling rules. Refunds and returns are governed by our
          <NuxtLink
            to="/refund"
            class="text-gold-800 underline"
          >Refund &amp; Cancellation Policy</NuxtLink>.
        </p>
      </section>

      <section>
        <h2 class="font-display text-xl text-ink">
          8. Limitation of liability
        </h2>
        <p class="mt-2">
          To the fullest extent permitted by law, {{ vendor.brandName }} is not liable for indirect or consequential losses arising from use of the Service
          or delayed delivery. Nothing in these Terms limits rights that cannot be excluded under applicable consumer law.
        </p>
      </section>

      <section>
        <h2 class="font-display text-xl text-ink">
          9. Changes &amp; contact
        </h2>
        <p class="mt-2">
          We may update these Terms; the “Last updated” date will change when we do. Continued use after changes means you accept the updated Terms.
          Questions:
          <NuxtLink
            to="/contact"
            class="text-gold-800 underline"
          >Contact us</NuxtLink>
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
