"""Outbound SMTP helpers — new-order alerts for packing / despatch."""

from __future__ import annotations

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr, parseaddr
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import Customer
from app.models.orders import SaleOrder, SaleOrderDetail

logger = logging.getLogger(__name__)


def smtp_configured() -> bool:
    s = get_settings()
    return bool(s.smtp_host and s.smtp_password and s.order_notify_recipients)


def _from_header() -> str:
    s = get_settings()
    raw = (s.smtp_from or s.smtp_user or "").strip()
    if not raw:
        return s.smtp_user
    name, addr = parseaddr(raw)
    if addr:
        return formataddr((name, addr)) if name else addr
    return raw


def send_email(
    *,
    to: list[str],
    subject: str,
    text_body: str,
    html_body: str | None = None,
    reply_to: str | None = None,
) -> bool:
    """Send one email. Returns False if SMTP is not configured or send fails."""
    settings = get_settings()
    recipients = [e.strip() for e in to if e and e.strip()]
    if not recipients:
        logger.warning("send_email skipped: no recipients")
        return False
    if not settings.smtp_host or not settings.smtp_password:
        logger.info("send_email skipped: SMTP not configured")
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = _from_header()
    msg["To"] = ", ".join(recipients)
    if reply_to and reply_to.strip():
        msg["Reply-To"] = reply_to.strip()
    msg.attach(MIMEText(text_body, "plain", "utf-8"))
    if html_body:
        msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=30) as server:
            if settings.smtp_use_tls:
                server.starttls()
            if settings.smtp_user:
                server.login(settings.smtp_user, settings.smtp_password)
            server.sendmail(settings.smtp_user or parseaddr(msg["From"])[1], recipients, msg.as_string())
        logger.info("Email sent to %s subject=%r", recipients, subject)
        return True
    except Exception:
        logger.exception("Failed to send email to %s subject=%r", recipients, subject)
        return False


def _escape(value: str) -> str:
    return (
        value.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def notify_contact_enquiry(
    *,
    name: str,
    email: str | None,
    phone: str | None,
    subject: str | None,
    message: str,
    vendor_name: str | None = None,
) -> bool:
    """Email site contact form submissions to ORDER_NOTIFY_TO (or SMTP_USER)."""
    settings = get_settings()
    recipients = settings.order_notify_recipients
    if not smtp_configured():
        logger.info("Contact notify skipped (SMTP/recipients not set)")
        return False

    name = (name or "").strip()
    email = (email or "").strip() or None
    phone = (phone or "").strip() or None
    subject_line = (subject or "").strip() or "Enquiry"
    message = (message or "").strip()
    brand = (vendor_name or "AS").strip() or "AS"

    mail_subject = f"[{brand}] Contact: {subject_line}"
    text_body = f"""New contact form enquiry.

Name:     {name}
Email:    {email or '—'}
Phone:    {phone or '—'}
Subject:  {subject_line}

Message:
{message}
"""
    html_body = f"""<html><body>
<p><strong>New contact form enquiry</strong></p>
<table cellpadding="4">
<tr><td>Name</td><td>{_escape(name)}</td></tr>
<tr><td>Email</td><td>{_escape(email or '—')}</td></tr>
<tr><td>Phone</td><td>{_escape(phone or '—')}</td></tr>
<tr><td>Subject</td><td>{_escape(subject_line)}</td></tr>
</table>
<p><strong>Message</strong></p>
<pre style="font-family:inherit;white-space:pre-wrap">{_escape(message)}</pre>
</body></html>"""

    try:
        return send_email(
            to=recipients,
            subject=mail_subject,
            text_body=text_body,
            html_body=html_body,
            reply_to=email,
        )
    except Exception:
        logger.exception("notify_contact_enquiry failed")
        return False


def _fmt_money(value: Any) -> str:
    try:
        return f"₹{float(value):,.2f}"
    except (TypeError, ValueError):
        return "₹0.00"


def _address_block(so: SaleOrder) -> str:
    parts = [
        so.shipping_name,
        so.shipping_street,
        ", ".join(p for p in [so.shipping_city, so.shipping_state, so.shipping_zip] if p),
        f"Phone: {so.shipping_phone}" if so.shipping_phone else None,
    ]
    return "\n".join(p for p in parts if p) or "(no shipping address)"


def notify_new_order(db: Session, so: SaleOrder) -> bool:
    """
    Email AS that a customer/trade order needs packing & despatch.
    Never raises — failures are logged so checkout is not blocked.
    """
    settings = get_settings()
    recipients = settings.order_notify_recipients
    if not smtp_configured():
        logger.info(
            "Order notify skipped (SMTP/recipients not set) order=%s",
            getattr(so, "order_code", so.id),
        )
        return False

    details = list(
        db.scalars(
            select(SaleOrderDetail).where(
                SaleOrderDetail.sale_order_id == so.id,
                SaleOrderDetail.vendor_id == so.vendor_id,
            )
        ).all()
    )
    customer = db.get(Customer, so.customer_id) if so.customer_id else None
    customer_label = ""
    if customer:
        customer_label = customer.name or ""
        if customer.email:
            customer_label = f"{customer_label} <{customer.email}>".strip()
        elif customer.phone:
            customer_label = f"{customer_label} ({customer.phone})".strip()

    lines_txt = "\n".join(
        f"  • {d.item_name or d.item_code or d.item_id} × {d.quantity} @ {_fmt_money(d.unit_price)}"
        for d in details
    ) or "  (no lines)"
    lines_html = "".join(
        f"<li>{d.item_name or d.item_code or d.item_id} × {d.quantity} "
        f"@ {_fmt_money(d.unit_price)}</li>"
        for d in details
    ) or "<li>(no lines)</li>"

    channel = so.sales_channel or "UNKNOWN"
    subject = f"[AS] New order {so.order_code} — pack & despatch"
    text_body = f"""A new order needs packing and despatch.

Order:     {so.order_code}
Channel:   {channel}
Date:      {so.order_date}
Status:    {so.status} / payment {so.payment_status} ({so.payment_method or '—'})
Total:     {_fmt_money(so.total_order_value)}
Shipping:  {_fmt_money(so.shipping_charge)}
Customer:  {customer_label or '—'}

Ship to:
{_address_block(so)}

Items:
{lines_txt}

Open Admin → Sales orders to confirm / update courier tracking.
"""
    html_body = f"""<html><body>
<p><strong>A new order needs packing and despatch.</strong></p>
<table cellpadding="4">
<tr><td>Order</td><td><strong>{so.order_code}</strong></td></tr>
<tr><td>Channel</td><td>{channel}</td></tr>
<tr><td>Date</td><td>{so.order_date}</td></tr>
<tr><td>Status</td><td>{so.status} / payment {so.payment_status} ({so.payment_method or '—'})</td></tr>
<tr><td>Total</td><td>{_fmt_money(so.total_order_value)}</td></tr>
<tr><td>Shipping</td><td>{_fmt_money(so.shipping_charge)}</td></tr>
<tr><td>Customer</td><td>{customer_label or '—'}</td></tr>
</table>
<p><strong>Ship to</strong><br/><pre style="font-family:inherit">{_address_block(so)}</pre></p>
<p><strong>Items</strong></p>
<ul>{lines_html}</ul>
<p>Open Admin → Sales orders to confirm / update courier tracking.</p>
</body></html>"""

    try:
        return send_email(
            to=recipients,
            subject=subject,
            text_body=text_body,
            html_body=html_body,
        )
    except Exception:
        logger.exception("notify_new_order failed for %s", so.order_code)
        return False
