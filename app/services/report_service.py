from datetime import date

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.customer import Customer
from app.models.enums import QuotationStatus
from app.models.quotation import Quotation
from app.schemas.dashboard import CustomerValue, MonthlyReportRow, StatusCount
from app.utils.calculations import money


class ReportService:
    def __init__(self, session: AsyncSession):
        self.session = session

    def _date_filters(self, stmt, date_from: date | None, date_to: date | None):
        if date_from:
            stmt = stmt.where(Quotation.quotation_date >= date_from)
        if date_to:
            stmt = stmt.where(Quotation.quotation_date <= date_to)
        return stmt

    async def quotation_summary(self, date_from: date | None, date_to: date | None) -> dict:
        stmt = select(
            func.count(Quotation.id),
            func.coalesce(func.sum(Quotation.grand_total), 0),
            func.coalesce(func.avg(Quotation.grand_total), 0),
        )
        stmt = self._date_filters(stmt, date_from, date_to)
        count, total, average = (await self.session.execute(stmt)).one()
        return {
            "quotation_count": count,
            "total_value": money(total),
            "average_value": money(average),
        }

    async def monthly(self, date_from: date | None, date_to: date | None) -> list[MonthlyReportRow]:
        stmt = select(
            func.year(Quotation.quotation_date),
            func.month(Quotation.quotation_date),
            func.count(Quotation.id),
            func.coalesce(func.sum(Quotation.grand_total), 0),
            func.coalesce(
                func.sum(
                    case(
                        (Quotation.status == QuotationStatus.APPROVED, Quotation.grand_total),
                        else_=0,
                    )
                ),
                0,
            ),
        ).group_by(func.year(Quotation.quotation_date), func.month(Quotation.quotation_date))
        stmt = self._date_filters(stmt, date_from, date_to).order_by(
            func.year(Quotation.quotation_date), func.month(Quotation.quotation_date)
        )
        rows = (await self.session.execute(stmt)).all()
        return [
            MonthlyReportRow(
                year=row[0],
                month=row[1],
                quotation_count=row[2],
                total_value=money(row[3]),
                approved_value=money(row[4]),
            )
            for row in rows
        ]

    async def customer_wise(self, date_from: date | None, date_to: date | None) -> list[CustomerValue]:
        stmt = (
            select(
                Customer.id,
                Customer.name,
                func.count(Quotation.id),
                func.coalesce(func.sum(Quotation.grand_total), 0),
            )
            .join(Quotation, Quotation.customer_id == Customer.id)
            .group_by(Customer.id, Customer.name)
            .order_by(func.sum(Quotation.grand_total).desc())
        )
        stmt = self._date_filters(stmt, date_from, date_to)
        rows = (await self.session.execute(stmt)).all()
        return [
            CustomerValue(
                customer_id=row[0],
                customer_name=row[1],
                quotation_count=row[2],
                total_value=money(row[3]),
            )
            for row in rows
        ]

    async def status_wise(self, date_from: date | None, date_to: date | None) -> list[StatusCount]:
        stmt = select(
            Quotation.status,
            func.count(Quotation.id),
            func.coalesce(func.sum(Quotation.grand_total), 0),
        ).group_by(Quotation.status)
        stmt = self._date_filters(stmt, date_from, date_to)
        rows = (await self.session.execute(stmt)).all()
        return [StatusCount(status=row[0], count=row[1], value=money(row[2])) for row in rows]
