from decimal import Decimal

from app.services.calculation_service import CalculationService, window_area_and_amount
from app.utils.calculations import calculate_item_amount


def test_item_amount_foundation_example():
    assert calculate_item_amount(Decimal("2000"), Decimal("900")) == Decimal("1800000.00")


def test_rcc_amount():
    assert calculate_item_amount(Decimal("2000"), Decimal("700")) == Decimal("1400000.00")


def test_full_quotation_example():
    calc = CalculationService()
    construction = calc.calculate_item_amount(Decimal("2000"), Decimal("900"))
    rcc = calc.calculate_item_amount(Decimal("2000"), Decimal("700"))
    summary = calc.summarize(
        construction=construction,
        additional=rcc,
        electrical=Decimal("0"),
        plumbing=Decimal("0"),
        doors=Decimal("0"),
        windows=Decimal("0"),
        tiles=Decimal("0"),
        granite=Decimal("0"),
        painting=Decimal("0"),
        discount_percentage=Decimal("5"),
        gst_percentage=Decimal("18"),
    )
    assert summary.subtotal == Decimal("3200000.00")
    assert summary.discount_amount == Decimal("160000.00")
    assert summary.taxable_amount == Decimal("3040000.00")
    assert summary.gst_amount == Decimal("547200.00")
    assert summary.grand_total == Decimal("3587200.00")


def test_window_area_formula():
    area, amount = window_area_and_amount(Decimal("5"), Decimal("4"), Decimal("300"))
    assert area == Decimal("20.00")
    assert amount == Decimal("6000.00")


def test_no_float_money():
    calc = CalculationService()
    amount = calc.calculate_item_amount(Decimal("0.1"), Decimal("0.2"))
    assert amount == Decimal("0.02")
    assert isinstance(amount, Decimal)
