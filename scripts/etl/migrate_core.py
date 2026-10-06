#!/usr/bin/env python3
"""MySQL (legacy Next/Prisma) → Postgres (as_app) core ETL.

Migrates: suppliers, items, customers (+ party mapping), customer addresses.
Does NOT migrate sale/purchase orders or stock ledger (re-seed or migrate later).

Usage:
  export MYSQL_URL='mysql://app:pass@127.0.0.1:3306/app_staging'
  export DATABASE_URL='postgresql://as:pass@127.0.0.1:5432/as_app'
  export TARGET_VENDOR_ID=1
  python migrate_core.py --dry-run
  python migrate_core.py --apply

Passwords in hash form are copied for staff users when --users is set
(bcrypt hashes from Next Auth / Prisma are compatible with as_app).
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from typing import Any
from urllib.parse import urlparse, unquote

PARTY_TYPES = {"DISTRIBUTOR", "DEALER", "CUSTOMER"}


def parse_mysql(url: str) -> dict[str, Any]:
    # mysql://user:pass@host:port/db
    u = urlparse(url.replace("mysql://", "http://", 1))
    return {
        "host": u.hostname or "127.0.0.1",
        "port": u.port or 3306,
        "user": unquote(u.username or "root"),
        "password": unquote(u.password or ""),
        "database": (u.path or "/").lstrip("/") or "app_staging",
    }


def parse_pg(url: str) -> str:
    # Accept postgresql+psycopg2:// or postgresql://
    return re.sub(r"^postgresql\+[^:]+://", "postgresql://", url)


def norm_party(raw: str | None) -> str:
    t = (raw or "CUSTOMER").strip().upper()
    if t not in PARTY_TYPES:
        return "CUSTOMER"
    return t


def connect_mysql(cfg: dict[str, Any]):
    import pymysql

    return pymysql.connect(
        host=cfg["host"],
        port=cfg["port"],
        user=cfg["user"],
        password=cfg["password"],
        database=cfg["database"],
        cursorclass=pymysql.cursors.DictCursor,
        charset="utf8mb4",
    )


def connect_pg(dsn: str):
    import psycopg2
    import psycopg2.extras

    conn = psycopg2.connect(dsn)
    conn.autocommit = False
    return conn


def fetch_all(cur, sql: str) -> list[dict[str, Any]]:
    cur.execute(sql)
    return list(cur.fetchall())


def migrate(dry_run: bool, include_users: bool) -> int:
    mysql_url = os.environ.get("MYSQL_URL") or os.environ.get("LEGACY_DATABASE_URL")
    pg_url = os.environ.get("DATABASE_URL") or os.environ.get("PG_URL")
    vendor_id = int(os.environ.get("TARGET_VENDOR_ID", "1"))

    if not mysql_url or not pg_url:
        print("Set MYSQL_URL and DATABASE_URL", file=sys.stderr)
        return 2

    mcfg = parse_mysql(mysql_url)
    pg_dsn = parse_pg(pg_url)

    print(f"MySQL {mcfg['host']}:{mcfg['port']}/{mcfg['database']} → PG vendor_id={vendor_id}")
    print(f"Mode: {'DRY-RUN' if dry_run else 'APPLY'}")

    mconn = connect_mysql(mcfg)
    try:
        with mconn.cursor() as mcur:
            suppliers = fetch_all(mcur, "SELECT * FROM suppliers ORDER BY id")
            items = fetch_all(mcur, "SELECT * FROM items ORDER BY id")
            customers = fetch_all(mcur, "SELECT * FROM customers ORDER BY id")
            addresses = fetch_all(mcur, "SELECT * FROM customer_addresses ORDER BY id")
            users = fetch_all(mcur, "SELECT * FROM users ORDER BY id") if include_users else []
    finally:
        mconn.close()

    print(
        f"Source counts: suppliers={len(suppliers)} items={len(items)} "
        f"customers={len(customers)} addresses={len(addresses)} users={len(users)}"
    )

    if dry_run:
        # Preview party mapping
        for c in customers[:5]:
            parent = c.get("ref_from") or 0
            print(
                f"  customer id={c['id']} type={norm_party(c.get('type'))} "
                f"parent={'null' if not parent else parent}"
            )
        if len(customers) > 5:
            print(f"  … {len(customers) - 5} more customers")
        print("Dry-run complete (no writes).")
        return 0

    pconn = connect_pg(pg_dsn)
    try:
        import psycopg2.extras

        with pconn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as pcur:
            # Suppliers (upsert by vendor_id + code)
            for s in suppliers:
                pcur.execute(
                    """
                    INSERT INTO suppliers (vendor_id, code, name, gstin, contact_person, address, phone, email)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (vendor_id, code) DO NOTHING
                    """,
                    (
                        vendor_id,
                        (s.get("code") or f"S{s['id']}").strip().upper()[:20],
                        s.get("name") or f"Supplier {s['id']}",
                        s.get("gstin"),
                        s.get("contact_person"),
                        s.get("address"),
                        s.get("phone"),
                        s.get("email"),
                    ),
                )

            # Items — unique on (vendor_id, code) if that constraint exists; else insert if missing
            for it in items:
                code = (it.get("code") or f"I{it['id']}")[:50]
                pcur.execute(
                    "SELECT id FROM items WHERE vendor_id=%s AND code=%s",
                    (vendor_id, code),
                )
                if pcur.fetchone():
                    continue
                pcur.execute(
                    """
                    INSERT INTO items (
                      vendor_id, code, name, description, unit_of_measure,
                      cost_price, sale_price, category, type, status,
                      is_sellable, is_online_sale, sale_price_includes_gst, primary_image
                    ) VALUES (
                      %s,%s,%s,%s,%s,%s,%s,%s,%s,'ACTIVE',%s,%s,%s,%s
                    )
                    """,
                    (
                        vendor_id,
                        code,
                        (it.get("name") or code)[:100],
                        it.get("description"),
                        it.get("unit_of_measure") or "PCS",
                        float(it.get("cost_price") or 0),
                        float(it.get("sale_price") or 0),
                        it.get("category") or "GENERAL",
                        it.get("type") or "PRODUCT",
                        bool(it.get("is_sellable", True)),
                        bool(it.get("is_online_sale", False)),
                        bool(it.get("sale_price_includes_gst", True)),
                        it.get("primary_image"),
                    ),
                )

            # Customers — two passes: insert without parent, then fix parents via legacy id map
            legacy_to_new: dict[int, int] = {}
            for c in customers:
                party = norm_party(c.get("type"))
                email = str(c["email"]).lower() if c.get("email") else None
                if email:
                    pcur.execute(
                        "SELECT id FROM customers WHERE vendor_id=%s AND email=%s",
                        (vendor_id, email),
                    )
                    existing = pcur.fetchone()
                    if existing:
                        legacy_to_new[int(c["id"])] = existing["id"]
                        continue
                pcur.execute(
                    """
                    INSERT INTO customers (
                      vendor_id, name, phone, gstin, email, party_type, parent_id,
                      acquisition_source, status
                    ) VALUES (%s,%s,%s,%s,%s,%s,NULL,%s,'ACTIVE')
                    RETURNING id
                    """,
                    (
                        vendor_id,
                        (c.get("name") or f"Customer {c['id']}")[:100],
                        c.get("phone"),
                        c.get("gstin"),
                        email,
                        party,
                        "OTHER",
                    ),
                )
                new_id = pcur.fetchone()["id"]
                legacy_to_new[int(c["id"])] = new_id

            for c in customers:
                ref = int(c.get("ref_from") or 0)
                if ref <= 0:
                    continue
                child = legacy_to_new.get(int(c["id"]))
                parent = legacy_to_new.get(ref)
                if not child or not parent:
                    continue
                pcur.execute(
                    "UPDATE customers SET parent_id=%s WHERE id=%s AND vendor_id=%s",
                    (parent, child, vendor_id),
                )

            for a in addresses:
                cust_legacy = int(a.get("customer_id") or 0)
                new_cust = legacy_to_new.get(cust_legacy)
                if not new_cust:
                    continue
                pcur.execute(
                    """
                    INSERT INTO customer_addresses (vendor_id, customer_id, street, city, state, zip, status)
                    VALUES (%s,%s,%s,%s,%s,%s,'ACTIVE')
                    """,
                    (
                        vendor_id,
                        new_cust,
                        a.get("street") or a.get("address_line1"),
                        a.get("city"),
                        a.get("state"),
                        a.get("zip") or a.get("pincode"),
                    ),
                )

            if include_users:
                staff_roles = {"ADMIN", "MANAGER", "STAFF"}
                for u in users:
                    role = (u.get("role") or "STAFF").upper()
                    if role == "SUPER_ADMIN":
                        continue
                    if role not in staff_roles:
                        role = "STAFF"
                    email = (u.get("email") or "").lower().strip()
                    if not email:
                        continue
                    pcur.execute("SELECT id FROM users WHERE email=%s", (email,))
                    if pcur.fetchone():
                        continue
                    pcur.execute(
                        """
                        INSERT INTO users (email, name, role, status, vendor_id, phone, password)
                        VALUES (%s,%s,%s,%s,%s,%s,%s)
                        """,
                        (
                            email,
                            (u.get("name") or email)[:100],
                            role,
                            (u.get("status") or "ACTIVE").upper(),
                            vendor_id,
                            u.get("phone"),
                            u.get("password") or "",
                        ),
                    )

        pconn.commit()
        print(f"Applied. Mapped {len(legacy_to_new)} customers into vendor {vendor_id}.")
    except Exception:
        pconn.rollback()
        raise
    finally:
        pconn.close()
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Legacy MySQL → as_app Postgres ETL (core tables)")
    ap.add_argument("--dry-run", action="store_true", help="Count/preview only")
    ap.add_argument("--apply", action="store_true", help="Write to Postgres")
    ap.add_argument("--users", action="store_true", help="Also copy staff users (hashed passwords)")
    args = ap.parse_args()
    if not args.dry_run and not args.apply:
        args.dry_run = True
    return migrate(dry_run=not args.apply, include_users=args.users)


if __name__ == "__main__":
    raise SystemExit(main())
