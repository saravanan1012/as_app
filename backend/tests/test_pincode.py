from app.core.pincode import lookup_pin, normalize_pin, state_from_pin
from app.services.pricing import (
    ecommerce_delivery_eta,
    normalize_shipping,
    shipping_charge_ecommerce,
)


def test_normalize_pin():
    assert normalize_pin("600001") == "600001"
    assert normalize_pin("600-001") == "600001"
    assert normalize_pin("60001") is None
    assert normalize_pin("abc") is None
    assert normalize_pin(None) is None


def test_state_from_known_prefixes():
    assert state_from_pin("600001") == "TN"
    assert state_from_pin("560001") == "KA"
    assert state_from_pin("110001") == "DL"
    assert state_from_pin("400001") == "MH"


def test_lookup_pin_unknown_prefix():
    # Valid 6-digit but outside mapped prefixes
    data = lookup_pin("999999")
    assert data is not None
    assert data["pin"] == "999999"
    assert data["state_code"] is None


def test_normalize_shipping_interstate_defaults():
    ship = normalize_shipping(
        {"ecommerce": {"enabled": True, "flat_rate": 80, "free_over": 500}}
    )
    eco = ship["ecommerce"]
    assert eco["flat_rate"] == 80
    assert eco["interstate_flat_rate"] == 160
    assert eco["eta_same_min"] == 2
    assert eco["eta_same_max"] == 4
    assert eco["eta_other_min"] == 5
    assert eco["eta_other_max"] == 7


def test_shipping_charge_same_vs_other_state():
    settings = {
        "shipping": {
            "ecommerce": {
                "enabled": True,
                "flat_rate": 60,
                "interstate_flat_rate": 120,
                "free_over_enabled": False,
            }
        }
    }
    same = shipping_charge_ecommerce(
        settings, subtotal=100, place_state="TN", vendor_state="TN"
    )
    other = shipping_charge_ecommerce(
        settings, subtotal=100, place_state="KA", vendor_state="TN"
    )
    missing_place = shipping_charge_ecommerce(
        settings, subtotal=100, place_state=None, vendor_state="TN"
    )
    assert same == 60
    assert other == 120
    assert missing_place == 60


def test_shipping_free_over_applies_both_zones():
    settings = {
        "shipping": {
            "ecommerce": {
                "enabled": True,
                "flat_rate": 60,
                "interstate_flat_rate": 120,
                "free_over_enabled": True,
                "free_over": 500,
            }
        }
    }
    assert (
        shipping_charge_ecommerce(
            settings, subtotal=500, place_state="KA", vendor_state="TN"
        )
        == 0
    )


def test_delivery_eta_zones():
    settings = {
        "shipping": {
            "ecommerce": {
                "flat_rate": 80,
                "eta_same_min": 2,
                "eta_same_max": 4,
                "eta_other_min": 5,
                "eta_other_max": 7,
            }
        }
    }
    same = ecommerce_delivery_eta(settings, vendor_state="TN", place_state="TN")
    other = ecommerce_delivery_eta(settings, vendor_state="TN", place_state="KA")
    assert same["delivery_zone"] == "same_state"
    assert same["delivery_eta_min"] == 2
    assert same["delivery_eta_max"] == 4
    assert other["delivery_zone"] == "other_state"
    assert other["delivery_eta_min"] == 5
    assert other["delivery_eta_max"] == 7
