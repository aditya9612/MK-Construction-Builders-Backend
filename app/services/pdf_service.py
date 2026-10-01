from app.services.quotation_service import QuotationService


class PdfService:
    """Preview payload for frontend PDF generation. Backend does not render PDFs."""

    def __init__(self, quotation_service: QuotationService):
        self.quotation_service = quotation_service

    async def preview(self, quotation_id: int) -> dict:
        return await self.quotation_service.preview(quotation_id)
