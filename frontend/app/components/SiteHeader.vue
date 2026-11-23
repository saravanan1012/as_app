<script setup lang="ts">
const vendor = useVendorStore()
const auth = useAuthStore()
const cart = useCartStore()
const { resolveHome } = useRedirect()

const isCustomer = computed(() => auth.user?.role === 'CUSTOMER')

const links = computed(() => {
  const items = [
    { label: 'Products', to: '/products' },
    { label: 'Contact', to: '/contact' }
  ]
  if (vendor.storeEnabled) {
    items.splice(1, 0, { label: 'Online Store', to: '/store' })
  }
  return items
})

const passwordOpen = ref(false)
const currentPassword = ref('')
const newPassword = ref('')
const confirmPassword = ref('')
const passwordError = ref('')
const passwordHint = ref('')
const passwordLoading = ref(false)

const initials = computed(() => {
  const name = auth.user?.name?.trim() || auth.user?.email || '?'
  const parts = name.split(/\s+/).filter(Boolean)
  if (parts.length >= 2) return (parts[0]![0]! + parts[1]![0]!).toUpperCase()
  return name.slice(0, 2).toUpperCase()
})

const accountItems = computed(() => {
  const items: Array<Array<Record<string, unknown>>> = [
    [
      {
        label: auth.user?.name || 'Account',
        description: auth.user?.email,
        type: 'label'
      }
    ],
    [
      {
        label: isCustomer.value ? 'My orders' : 'Account home',
        icon: 'i-lucide-package',
        to: isCustomer.value ? '/store/orders' : resolveHome()
      },
      {
        label: 'Change password',
        icon: 'i-lucide-key-round',
        onSelect: () => {
          passwordError.value = ''
          passwordHint.value = ''
          currentPassword.value = ''
          newPassword.value = ''
          confirmPassword.value = ''
          passwordOpen.value = true
        }
      }
    ],
    [
      {
        label: 'Logout',
        icon: 'i-lucide-log-out',
        color: 'error',
        onSelect: async () => {
          await auth.logout()
          await navigateTo('/login')
        }
      }
    ]
  ]
  return items
})

async function submitPassword() {
  passwordError.value = ''
  passwordHint.value = ''
  if (newPassword.value.length < 6) {
    passwordError.value = 'New password must be at least 6 characters.'
    return
  }
  if (newPassword.value !== confirmPassword.value) {
    passwordError.value = 'New password and confirmation do not match.'
    return
  }
  passwordLoading.value = true
  try {
    await auth.changePassword(currentPassword.value, newPassword.value)
    passwordHint.value = 'Password updated.'
    currentPassword.value = ''
    newPassword.value = ''
    confirmPassword.value = ''
    setTimeout(() => {
      passwordOpen.value = false
      passwordHint.value = ''
    }, 800)
  } catch (e: unknown) {
    passwordError.value
      = (e as { data?: { message?: string } })?.data?.message || 'Could not update password'
  } finally {
    passwordLoading.value = false
  }
}
</script>

<template>
  <header class="sticky top-0 z-40 border-b border-gold-300/60 bg-gold-100/85 backdrop-blur-md">
    <div class="mx-auto flex h-14 max-w-6xl items-center justify-between gap-4 px-4 sm:h-16 sm:px-6">
      <NuxtLink
        to="/"
        class="flex items-center gap-2 text-ink"
        :aria-label="vendor.brandName"
      >
        <img
          src="/images/logo-header.png"
          alt=""
          width="40"
          height="40"
          class="h-9 w-9 shrink-0 object-contain sm:h-10 sm:w-10"
        >
        <span class="font-display hidden text-xl tracking-tight sm:inline sm:text-2xl">
          {{ vendor.brandName }}
        </span>
      </NuxtLink>

      <nav class="hidden items-center gap-6 text-sm font-medium text-ink-muted md:flex">
        <NuxtLink
          v-for="link in links"
          :key="link.to"
          :to="link.to"
          class="transition-colors hover:text-ink"
          active-class="text-ink"
        >
          {{ link.label }}
        </NuxtLink>
      </nav>

      <div class="flex items-center gap-2">
        <NuxtLink
          v-if="vendor.storeEnabled"
          to="/store/cart"
          class="relative inline-flex h-10 items-center justify-center rounded-full px-2 text-sm font-medium text-ink transition hover:bg-gold-300/50"
          aria-label="Cart"
        >
          Cart
          <span
            v-if="cart.count"
            class="ml-1 flex h-5 min-w-5 items-center justify-center rounded-full bg-gold-700 px-1 text-[11px] font-semibold text-white"
          >
            {{ cart.count }}
          </span>
        </NuxtLink>

        <UDropdownMenu
          v-if="auth.isLoggedIn"
          :items="accountItems"
          :content="{ align: 'end', sideOffset: 8 }"
        >
          <UTooltip
            :text="auth.user?.name || 'Account'"
            :content="{ side: 'bottom' }"
          >
            <UButton
              color="neutral"
              variant="ghost"
              size="sm"
              square
              aria-label="Account menu"
              :title="auth.user?.name || 'Account'"
            >
              <UAvatar
                :text="initials"
                size="xs"
                class="bg-gold-700 text-white"
              />
            </UButton>
          </UTooltip>
        </UDropdownMenu>
        <template v-else>
          <UButton
            v-if="vendor.storeEnabled"
            to="/store/register"
            size="sm"
            color="neutral"
            variant="ghost"
          >
            Register
          </UButton>
          <UButton
            to="/login"
            size="sm"
            color="primary"
          >
            Login
          </UButton>
        </template>
      </div>
    </div>

    <nav class="flex gap-4 overflow-x-auto border-t border-gold-300/40 px-4 py-2 text-sm text-ink-muted md:hidden">
      <NuxtLink
        v-for="link in links"
        :key="link.to"
        :to="link.to"
        class="whitespace-nowrap"
      >
        {{ link.label }}
      </NuxtLink>
    </nav>

    <UModal
      v-model:open="passwordOpen"
      title="Change password"
      description="Enter your current password, then choose a new one."
    >
      <template #body>
        <form
          class="space-y-4"
          @submit.prevent="submitPassword"
        >
          <UFormField label="Current password">
            <UInput
              v-model="currentPassword"
              type="password"
              required
              autocomplete="current-password"
              class="w-full"
            />
          </UFormField>
          <UFormField label="New password">
            <UInput
              v-model="newPassword"
              type="password"
              required
              minlength="6"
              autocomplete="new-password"
              class="w-full"
            />
          </UFormField>
          <UFormField label="Confirm new password">
            <UInput
              v-model="confirmPassword"
              type="password"
              required
              minlength="6"
              autocomplete="new-password"
              class="w-full"
            />
          </UFormField>
          <p
            v-if="passwordError"
            class="text-sm text-red-700"
          >
            {{ passwordError }}
          </p>
          <p
            v-if="passwordHint"
            class="text-sm text-ink"
          >
            {{ passwordHint }}
          </p>
        </form>
      </template>
      <template #footer="{ close }">
        <div class="flex justify-end gap-2">
          <UButton
            color="neutral"
            variant="ghost"
            @click="close()"
          >
            Cancel
          </UButton>
          <UButton
            :loading="passwordLoading"
            @click="submitPassword"
          >
            Update password
          </UButton>
        </div>
      </template>
    </UModal>
  </header>
</template>
