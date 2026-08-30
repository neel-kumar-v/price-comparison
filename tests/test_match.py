"""Tests for product matching (no browser required)."""

from price_compare.match import ProductReference, load_fixture, verify_same_product


def test_general_hask_match():
    ref = load_fixture("tests/fixtures/products.json", "general")
    result = verify_same_product(
        ref,
        "HASK Repair + Argan Oil Repairing Conditioner, 16 fl oz",
        observed_upc="071164341568",
    )
    assert result.same_product
    assert result.confidence == "high"


def test_shoes_match():
    ref = load_fixture("tests/fixtures/products.json", "shoes")
    ref = ProductReference(**{**ref.__dict__, "colorway": "Black/White"})
    result = verify_same_product(ref, "Nike Pegasus 41 Men's Running Shoes - Black/White - Size 10.5")
    assert result.same_product


def test_tech_sku_match():
    ref = load_fixture("tests/fixtures/products.json", "tech")
    result = verify_same_product(ref, "Apple AirPods Pro 2", observed_sku="MTJV3LL/A")
    assert result.same_product
    assert result.confidence == "high"


def test_tech_rejects_refurb():
    ref = load_fixture("tests/fixtures/products.json", "tech")
    result = verify_same_product(ref, "Apple AirPods Pro Renewed", observed_sku="MTJV3LL/A")
    assert not result.same_product


def test_grocery_match():
    ref = load_fixture("tests/fixtures/products.json", "grocery")
    result = verify_same_product(ref, "Organic Whole Milk", observed_size="1 gal")
    assert result.same_product
