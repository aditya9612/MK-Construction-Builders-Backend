from decimal import Decimal

from app.schemas.quotation import CalculationSummary
from app.utils.calculations import (
    ZERO,
    calculate_discount,
    calculate_grand_total,
    calculate_gst,
    calculate_item_amount,
    calculate_window_area,
    money,
)


class CalculationService:
    @staticmethod
    def calculate_item_amount(quantity: Decimal, rate: Decimal) -> Decimal:
        return calculate_item_amount(quantity, rate)

    @staticmethod
    def calculate_section_total(amounts: list[Decimal]) -> Decimal:
        total = ZERO
        for amount in amounts:
            total += money(amount)
        return money(total)

    def calculate_construction_total(self, items: list) -> Decimal:
        return self.calculate_section_total([item.amount for item in items])

    def calculate_additional_total(self, items: list) -> Decimal:
        return self.calculate_section_total([item.amount for item in items])

    def calculate_electrical_total(self, items: list) -> Decimal:
        return self.calculate_section_total([item.amount for item in items])

    def calculate_plumbing_total(self, items: list) -> Decimal:
        return self.calculate_section_total([item.amount for item in items])

    def calculate_door_total(self, items: list) -> Decimal:
        return self.calculate_section_total([item.amount for item in items])

    def calculate_window_total(self, items: list) -> Decimal:
        return self.calculate_section_total([item.amount for item in items])

    def calculate_tile_total(self, items: list) -> Decimal:
        return self.calculate_section_total([item.amount for item in items])

    def calculate_granite_total(self, items: list) -> Decimal:
        return self.calculate_section_total([item.amount for item in items])

    def calculate_painting_total(self, items: list) -> Decimal:
        return self.calculate_section_total([item.amount for item in items])

    def calculate_subtotal(self, sections: dict[str, Decimal]) -> Decimal:
        return money(sum((money(v) for v in sections.values()), ZERO))

    def calculate_discount(self, subtotal: Decimal, discount_percentage: Decimal) -> Decimal:
        return calculate_discount(subtotal, discount_percentage)

    def calculate_gst(self, taxable_amount: Decimal, gst_percentage: Decimal) -> Decimal:
        return calculate_gst(taxable_amount, gst_percentage)

    def calculate_grand_total(self, taxable_amount: Decimal, gst_amount: Decimal) -> Decimal:
        return calculate_grand_total(taxable_amount, gst_amount)

    def summarize(
        self,
        *,
        construction: Decimal,
        additional: Decimal,
        electrical: Decimal,
        plumbing: Decimal,
        doors: Decimal,
        windows: Decimal,
        tiles: Decimal,
        granite: Decimal,
        painting: Decimal,
        discount_percentage: Decimal,
        gst_percentage: Decimal,
    ) -> CalculationSummary:
        subtotal = self.calculate_subtotal(
            {
                "construction": construction,
                "additional": additional,
                "electrical": electrical,
                "plumbing": plumbing,
                "doors": doors,
                "windows": windows,
                "tiles": tiles,
                "granite": granite,
                "painting": painting,
            }
        )
        discount_amount = self.calculate_discount(subtotal, discount_percentage)
        taxable_amount = money(subtotal - discount_amount)
        gst_amount = self.calculate_gst(taxable_amount, gst_percentage)
        grand_total = self.calculate_grand_total(taxable_amount, gst_amount)
        return CalculationSummary(
            construction_total=construction,
            additional_total=additional,
            electrical_total=electrical,
            plumbing_total=plumbing,
            door_total=doors,
            window_total=windows,
            tile_total=tiles,
            granite_total=granite,
            painting_total=painting,
            subtotal=subtotal,
            discount_percentage=money(discount_percentage),
            discount_amount=discount_amount,
            taxable_amount=taxable_amount,
            gst_percentage=money(gst_percentage),
            gst_amount=gst_amount,
            grand_total=grand_total,
        )


def window_area_and_amount(length: Decimal, width: Decimal, rate: Decimal) -> tuple[Decimal, Decimal]:
    area = calculate_window_area(length, width)
    return area, calculate_item_amount(area, rate)
