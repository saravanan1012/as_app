<script setup lang="ts">
const vendor = useVendorStore()
const lastUpdated = '31 October 2026'

useSeoMeta({
  title: () => `Refund Policy · ${vendor.brandName}`,
  description: () =>
    `Refund and cancellation rules for ${vendor.brandName} Online Store orders paid by COD or Razorpay.`
})
</script>

<template>
  <div class="mx-auto max-w-3xl px-4 py-10 sm:px-6 sm:py-14">
    <div class="flex flex-wrap items-end justify-between gap-4">
      <div>
        <h1 class="font-display text-4xl text-ink">
          Refund &amp; Cancellation Policy
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
        <h2 class="font-display text-xl text-ink">
          1. Scope
        </h2>
        <p class="mt-2">
          This policy applies to Online Store orders for {{ vendor.brandName }} products (including sanitary napkins)
          paid by Cash on Delivery (COD) or prepaid via Razorpay. It does not cover wholesale / B2B trade terms unless stated separately.
        </p>
      </section>

      <section>
        <h2 class="font-display text-xl text-ink">
          2. Cancellation before dispatch
        </h2>
        <p class="mt-2">
          You may request cancellation before the order is packed or handed to the courier by contacting us with your order code
          (see
          <NuxtLink
            to="/store/orders"
            class="text-gold-800 underline"
          >/store/orders</NuxtLink>
          when signed in, or
          <NuxtLink
            to="/contact"
            class="text-gold-800 underline"
          >Contact</NuxtLink>).
          Once shipped, cancellation is not usually possible; see returns below.
        </p>
      </section>

      <section>
        <h2 class="font-display text-xl text-ink">
          3. Hygiene products
        </h2>
        <p class="mt-2">
          For health and safety, <strong class="text-ink">opened or used sanitary napkins and sealed personal-care packs that have been opened</strong>
          are generally not returnable. We may accept a return or replacement when:
        </p>
        <ul class="mt-2 list-disc space-y-1 pl-5">
          <li>You received a damaged, defective, or wrong item (size / SKU mismatch)</li>
          <li>The sealed pack arrived visibly broken in transit</li>
          <li>Applicable law requires a remedy</li>
        </ul>
        <p class="mt-2">
          Please report issues within <strong class="text-ink">7 days</strong> of delivery with clear photos of the pack, shipping label, and order code.
        </p>
      </section>

      <section>
        <h2 class="font-display text-xl text-ink">
          4. COD orders
        </h2>
        <p class="mt-2">
          COD orders that are cancelled before dispatch incur no payment. Repeated refusals of COD deliveries may lead to prepaid-only checkout for future orders.
          If you already paid a COD amount to the courier for a wrong/damaged item we approve for refund, we will process a refund after we receive the return (if required) and verify the claim.
        </p>
      </section>

      <section>
        <h2 class="font-display text-xl text-ink">
          5. Prepaid Razorpay orders
        </h2>
        <p class="mt-2">
          For approved refunds on Razorpay payments, we initiate a refund to the original payment method.
          Banking timelines typically take <strong class="text-ink">5–10 business days</strong> after we process the refund in Razorpay
          (sometimes longer depending on your bank or UPI app). Duplicate or failed charges should be reported promptly with the Razorpay payment ID.
        </p>
      </section>

      <section>
        <h2 class="font-display text-xl text-ink">
          6. How to request
        </h2>
        <p class="mt-2">
          Use
          <NuxtLink
            to="/contact"
            class="text-gold-800 underline"
          >Contact</NuxtLink>
          and include: registered email, order code, Razorpay payment ID (if prepaid), and a short description with photos when relevant.
          We respond as soon as practical during business hours.
        </p>
      </section>

      <section>
        <h2 class="font-display text-xl text-ink">
          7. Related policies
        </h2>
        <p class="mt-2">
          <NuxtLink
            to="/terms"
            class="text-gold-800 underline"
          >Terms of Service</NuxtLink>
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
