import { jsPDF } from 'jspdf'
import autoTable from 'jspdf-autotable'

export type InvoiceSeller = {
  companyName: string
  gstin?: string | null
  addressLines: string[]
  phone?: string
  email?: string
}

export type InvoiceCustomer = {
  name?: string | null
  gstin?: string | null
  phone?: string | null
  email?: string | null
  street?: string | null
  city?: string | null
  zip?: string | null
  state?: string | null
}

export type InvoiceOrder = {
  order_code: string
  order_date?: string
  sales_channel?: string | null
  status?: string
  payment_status?: string
  total_gross_amount: number
  total_discount_amount: number
  total_net_amount: number
  total_tax_amount: number
  shipping_charge: number
  handling_charge: number
  total_order_value: number
  items: Array<{
    item_id: number
    item_name?: string | null
    quantity: number
    unit_price: number
    discount_amount: number
    gst_rate: number
    gst_amount: number
    net_line_total: number
  }>
}

function safeFilename(code: string) {
  return code.replace(/[^\w.-]+/g, '_').slice(0, 80) || 'invoice'
}

export function downloadSaleOrderInvoicePdf(
  seller: InvoiceSeller,
  customer: InvoiceCustomer | null,
  order: InvoiceOrder
) {
  const doc = new jsPDF({ unit: 'mm', format: 'a4' })
  const pageW = doc.internal.pageSize.getWidth()
  const margin = 14
  const col2 = pageW / 2 + 4

  doc.setFontSize(16)
  doc.setFont('helvetica', 'bold')
  doc.text('Tax Invoice', margin, 18)

  doc.setFontSize(9)
  let y = 26
  doc.setFont('helvetica', 'bold')
  doc.text('From', margin, y)
  doc.text('Bill to', col2, y)
  y += 5

  let leftY = y
  let rightY = y
  doc.setFont('helvetica', 'normal')
  doc.text(seller.companyName, margin, leftY)
  doc.text(customer?.name || 'Unknown', col2, rightY)
  leftY += 5
  rightY += 5

  if (seller.gstin) {
    doc.text(`GSTIN: ${seller.gstin}`, margin, leftY)
    leftY += 5
  }
  if (customer?.gstin) {
    doc.text(`GSTIN: ${customer.gstin}`, col2, rightY)
    rightY += 5
  }

  for (const line of seller.addressLines) {
    doc.text(line, margin, leftY)
    leftY += 4
  }

  const addr = [customer?.street, customer?.city, customer?.state, customer?.zip]
    .filter(Boolean)
    .join(', ') || 'Address not on file'
  for (const tline of doc.splitTextToSize(addr, pageW - col2 - margin + 4)) {
    doc.text(tline, col2, rightY)
    rightY += 4
  }

  if (seller.phone || seller.email) {
    doc.text([seller.phone, seller.email].filter(Boolean).join(' · '), margin, leftY)
    leftY += 5
  }
  if (customer?.phone || customer?.email) {
    doc.text([customer.phone, customer.email].filter(Boolean).join(' · '), col2, rightY)
    rightY += 5
  }

  y = Math.max(leftY, rightY) + 6
  doc.setFont('helvetica', 'bold')
  doc.text('Order details', margin, y)
  y += 5
  doc.setFont('helvetica', 'normal')
  doc.text(
    `Order: ${order.order_code}   Date: ${order.order_date || '—'}   Channel: ${order.sales_channel || '—'}`,
    margin,
    y
  )
  y += 5
  doc.text(`Status: ${order.status || '—'}   Payment: ${order.payment_status || '—'}`, margin, y)
  y += 8

  autoTable(doc, {
    startY: y,
    head: [['#', 'Item', 'Qty', 'Unit', 'Disc.', 'GST %', 'GST', 'Total']],
    body: order.items.map((line, i) => [
      String(i + 1),
      line.item_name || String(line.item_id),
      String(line.quantity),
      Number(line.unit_price).toFixed(2),
      Number(line.discount_amount).toFixed(2),
      `${Number(line.gst_rate) || 0}%`,
      Number(line.gst_amount).toFixed(2),
      Number(line.net_line_total).toFixed(2)
    ]),
    styles: { fontSize: 8, cellPadding: 1.5 },
    headStyles: { fillColor: [184, 155, 106] },
    columnStyles: {
      2: { halign: 'right' },
      3: { halign: 'right' },
      4: { halign: 'right' },
      5: { halign: 'right' },
      6: { halign: 'right' },
      7: { halign: 'right' }
    }
  })

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  let ty = ((doc as any).lastAutoTable?.finalY || y) + 8
  const amtX = pageW - margin
  const row = (label: string, value: string, bold = false) => {
    doc.setFont('helvetica', bold ? 'bold' : 'normal')
    doc.text(label, margin, ty)
    doc.text(value, amtX, ty, { align: 'right' })
    ty += 5.5
  }
  doc.setFontSize(9)
  row('Gross total', Number(order.total_gross_amount).toFixed(2))
  row('Total discount', Number(order.total_discount_amount).toFixed(2))
  row('Net', Number(order.total_net_amount).toFixed(2))
  row('GST / tax', Number(order.total_tax_amount).toFixed(2))
  row('Shipping', Number(order.shipping_charge || 0).toFixed(2))
  row('Handling', Number(order.handling_charge || 0).toFixed(2))
  row('Grand total', Number(order.total_order_value).toFixed(2), true)

  doc.save(`invoice-${safeFilename(order.order_code)}.pdf`)
}
