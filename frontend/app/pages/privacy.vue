<script setup lang="ts">
const vendor = useVendorStore()
const lastUpdated = '31 October 2026'

useSeoMeta({
  title: () => `Privacy Policy · ${vendor.brandName}`,
  description: () =>
    `How ${vendor.brandName} collects and uses account, order, and payment information for our online store.`
})
</script>

<template>
  <div class="mx-auto max-w-3xl px-4 py-10 sm:px-6 sm:py-14">
    <div class="flex flex-wrap items-end justify-between gap-4">
      <div>
        <h1 class="font-display text-4xl text-ink">
          Privacy Policy
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
          1. Overview
        </h2>
        <p class="mt-2">
          This Privacy Policy explains how {{ vendor.brandName }} (“we”, “us”) collects, uses, and shares information
          when you browse our website, create an account, or buy products through our Online Store (including
          sanitary napkins and related items). By using the Service, you agree to this policy. Service rules are in our
          <NuxtLink
            to="/terms"
            class="text-gold-800 underline"
          >Terms of Service</NuxtLink>.
        </p>
      </section>

      <section>
        <h2 class="font-display text-xl text-ink">
          2. Information we collect
        </h2>
        <ul class="mt-2 list-disc space-y-1 pl-5">
          <li>
            <strong class="text-ink">Account data:</strong> name, email, phone, and password (stored hashed) when you register or log in
          </li>
          <li>
            <strong class="text-ink">Order &amp; shipping data:</strong> shipping name, address, city, PIN, state, phone, and items ordered
          </li>
          <li>
            <strong class="text-ink">Contact messages:</strong> details you send via our
            <NuxtLink
              to="/contact"
              class="text-gold-800 underline"
            >Contact</NuxtLink> page
          </li>
          <li>
            <strong class="text-ink">Payment metadata:</strong> transaction references and status via Razorpay (UPI / cards / wallets).
            We do not store full card numbers on our servers; card and UPI data are handled by Razorpay
          </li>
          <li>
            <strong class="text-ink">Technical data:</strong> basic device/browser information, cookies or similar storage needed for login session and cart
          </li>
        </ul>
      </section>

      <section>
        <h2 class="font-display text-xl text-ink">
          3. How we use information
        </h2>
        <ul class="mt-2 list-disc space-y-1 pl-5">
          <li>Process and fulfil Online Store orders (including COD and prepaid Razorpay payments)</li>
          <li>Provide customer support, refunds, and order updates</li>
          <li>Improve product pages, store experience, and security</li>
          <li>Comply with legal and tax obligations</li>
        </ul>
      </section>

      <section>
        <h2 class="font-display text-xl text-ink">
          4. Sharing
        </h2>
        <p class="mt-2">
          We may share limited data with payment processors (Razorpay), logistics/courier partners for delivery,
          and hosting/infrastructure providers who process data on our behalf. We do not sell your personal information.
        </p>
      </section>

      <section>
        <h2 class="font-display text-xl text-ink">
          5. Retention &amp; security
        </h2>
        <p class="mt-2">
          We retain account and order records as needed for operations, accounting, and legal requirements.
          We use reasonable technical and organisational measures to protect data; no method of transmission is 100% secure.
        </p>
      </section>

      <section>
        <h2 class="font-display text-xl text-ink">
          6. Your choices
        </h2>
        <p class="mt-2">
          You may update account details where the Service allows, or contact us to request access or correction of personal data we hold,
          subject to applicable law. You can clear cart data in your browser; login cookies are required while signed in.
        </p>
      </section>

      <section>
        <h2 class="font-display text-xl text-ink">
          7. Contact
        </h2>
        <p class="mt-2">
          Questions about this policy:
          <NuxtLink
            to="/contact"
            class="text-gold-800 underline"
          >Contact us</NuxtLink>.
          Also see our
          <NuxtLink
            to="/refund"
            class="text-gold-800 underline"
          >Refund Policy</NuxtLink>.
        </p>
      </section>
    </div>
  </div>
</template>
