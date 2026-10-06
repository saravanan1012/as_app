<script setup lang="ts">
const vendor = useVendorStore()
</script>

<template>
  <div class="mx-auto max-w-3xl px-4 py-14 sm:px-6">
    <h1 class="font-display text-4xl text-ink">
      Contact
    </h1>
    <p class="mt-3 text-ink-muted">
      Reach {{ vendor.brandName }} for wholesale, stockists, or product questions.
    </p>
    <dl class="mt-10 space-y-6 text-ink">
      <div>
        <dt class="text-sm uppercase tracking-wider text-ink-muted">
          Company
        </dt>
        <dd class="mt-1 font-display text-2xl">
          {{ vendor.vendor?.legal_name || vendor.brandName }}
        </dd>
      </div>
      <div v-if="vendor.vendor?.address">
        <dt class="text-sm uppercase tracking-wider text-ink-muted">
          Address
        </dt>
        <dd class="mt-1 whitespace-pre-line">
          {{ vendor.vendor.address }}
        </dd>
      </div>
      <div>
        <dt class="text-sm uppercase tracking-wider text-ink-muted">
          Visit
        </dt>
        <dd class="mt-1">
          Product information is always available.
          <NuxtLink
            v-if="vendor.storeEnabled"
            to="/store"
            class="text-gold-800 underline-offset-4 hover:underline"
          >
            Shop online when Store is open.
          </NuxtLink>
        </dd>
      </div>
    </dl>
  </div>
</template>
