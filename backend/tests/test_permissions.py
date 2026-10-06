from app.core.permissions import permission_implies


def test_manage_implies_write_and_read():
    have = {"sales.orders.manage"}
    assert permission_implies(have, "sales.orders.manage")
    assert permission_implies(have, "sales.orders.write")
    assert permission_implies(have, "sales.orders.read")


def test_write_implies_read():
    have = {"stock.write"}
    assert permission_implies(have, "stock.read")
    assert not permission_implies(have, "stock.manage")


def test_exact_match():
    have = {"ecommerce.store.read"}
    assert permission_implies(have, "ecommerce.store.read")
    assert not permission_implies(have, "customers.read")
