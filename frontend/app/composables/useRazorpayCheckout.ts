/**
 * Load Razorpay Checkout.js and open payment for an order created by the API.
 */
type RazorpaySuccessResponse = {
  razorpay_order_id: string
  razorpay_payment_id: string
  razorpay_signature: string
}

type CheckoutOptions = {
  key: string
  orderId: string
  amount: number
  currency?: string
  name?: string
  description?: string
  prefillEmail?: string
  prefillContact?: string
  prefillName?: string
}

declare global {
  interface Window {
    Razorpay?: new (options: Record<string, unknown>) => { open: () => void }
  }
}

function loadRazorpayScript(): Promise<void> {
  if (typeof window === 'undefined') {
    return Promise.reject(new Error('Razorpay requires a browser'))
  }
  if (window.Razorpay) return Promise.resolve()

  return new Promise((resolve, reject) => {
    const existing = document.querySelector<HTMLScriptElement>('script[data-razorpay]')
    if (existing) {
      existing.addEventListener('load', () => resolve())
      existing.addEventListener('error', () => reject(new Error('Failed to load Razorpay')))
      return
    }
    const script = document.createElement('script')
    script.src = 'https://checkout.razorpay.com/v1/checkout.js'
    script.async = true
    script.dataset.razorpay = '1'
    script.onload = () => resolve()
    script.onerror = () => reject(new Error('Failed to load Razorpay'))
    document.head.appendChild(script)
  })
}

export function useRazorpayCheckout() {
  async function openCheckout(opts: CheckoutOptions): Promise<RazorpaySuccessResponse> {
    await loadRazorpayScript()
    if (!window.Razorpay) {
      throw new Error('Razorpay SDK unavailable')
    }
    if (!opts.key) {
      throw new Error('Razorpay key is not configured on the server')
    }

    return new Promise((resolve, reject) => {
      const rzp = new window.Razorpay!({
        key: opts.key,
        amount: opts.amount,
        currency: opts.currency || 'INR',
        name: opts.name || 'AS Organic',
        description: opts.description || 'Online Store order',
        order_id: opts.orderId,
        prefill: {
          email: opts.prefillEmail || '',
          contact: opts.prefillContact || '',
          name: opts.prefillName || ''
        },
        handler(response: RazorpaySuccessResponse) {
          resolve(response)
        },
        modal: {
          ondismiss() {
            reject(new Error('Payment cancelled'))
          }
        }
      })
      rzp.open()
    })
  }

  return { openCheckout }
}
