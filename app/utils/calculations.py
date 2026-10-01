from decimal import ROUND_HALF_UP, Decimal

TWO_PLACES = Decimal("0.01")
ZERO = Decimal("0.00")


def money(value: Decimal | int | str | float) -> Decimal:
    return Decimal(str(value)).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)


def calculate_item_amount(quantity: Decimal, rate: Decimal) -> Decimal:
    return money(Decimal(str(quantity)) * Decimal(str(rate)))


def calculate_window_area(length: Decimal, width: Decimal) -> Decimal:
    return money(Decimal(str(length)) * Decimal(str(width)))


def calculate_discount(subtotal: Decimal, discount_percentage: Decimal) -> Decimal:
    return money(subtotal * Decimal(str(discount_percentage)) / Decimal("100"))


def calculate_gst(taxable_amount: Decimal, gst_percentage: Decimal) -> Decimal:
    return money(taxable_amount * Decimal(str(gst_percentage)) / Decimal("100"))


def calculate_grand_total(taxable_amount: Decimal, gst_amount: Decimal) -> Decimal:
    return money(taxable_amount + gst_amount)
