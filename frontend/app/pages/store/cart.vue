<script setup lang="ts">
definePageMeta({ middleware: ['store-enabled'] })

const cart = useCartStore()
</script>

<template>
  <div class="mx-auto max-w-2xl px-4 py-10 sm:px-6">
    <h1 class="font-display text-4xl text-ink">
      Cart
    </h1>

    <ul
      v-if="cart.lines.length"
      class="mt-8 divide-y divide-gold-300/70 border-y border-gold-300/70"
    >
      <li
        v-for="line in cart.lines"
        :key="line.item_id"
        class="flex items-center justify-between gap-4 py-4"
      >
        <div>
          <p class="font-medium text-ink">
            {{ line.name }}
          </p>
          <p class="text-sm text-ink-muted">
            ₹{{ line.sale_price.toFixed(0) }}
          </p>
        </div>
        <div class="flex items-center gap-2">
          <UButton
            icon="i-lucide-minus"
            size="sm"
            color="neutral"
            variant="soft"
            @click="cart.setQty(line.item_id, line.quantity - 1)"
          />
          <span class="w-8 text-center tabular-nums">{{ line.quantity }}</span>
          <UButton
            icon="i-lucide-plus"
            size="sm"
            color="neutral"
            variant="soft"
            @click="cart.setQty(line.item_id, line.quantity + 1)"
          />
        </div>
      </li>
    </ul>

    <p
      v-else
      class="mt-10 text-ink-muted"
    >
      Your cart is empty.
      <NuxtLink
        to="/store"
        class="text-gold-800 underline-offset-2 hover:underline"
      >
        Continue shopping
      </NuxtLink>
    </p>

    <div
      v-if="cart.lines.length"
      class="mt-8 flex flex-wrap items-center justify-between gap-4"
    >
      <p class="text-lg font-semibold text-ink">
        Subtotal ₹{{ cart.subtotal.toFixed(0) }}
      </p>
      <UButton
        to="/store/checkout"
        size="xl"
      >
        Checkout
      </UButton>
    </div>
  </div>
</template>
