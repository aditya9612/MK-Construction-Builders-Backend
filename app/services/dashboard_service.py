from datetime import date

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.customer import Customer
from app.models.enums import QuotationStatus
from app.models.quotation import Quotation
from app.schemas.dashboard import CustomerValue, DashboardSummary, StatusCount
from app.schemas.quotation import QuotationListItem
from app.utils.calculations import ZERO, money


class DashboardService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def summary(self) -> DashboardSummary:
        today = date.today()
        month_start = today.replace(day=1)

        total = (await self.session.execute(select(func.count(Quotation.id)))).scalar_one()
        totals_by_status = (
            await self.session.execute(
                select(Quotation.status, func.count(Quotation.id), func.coalesce(func.sum(Quotation.grand_total), 0))
                .group_by(Quotation.status)
            )
        ).all()
        status_map = {row[0]: (row[1], money(row[2])) for row in totals_by_status}

        def count_for(status: str) -> int:
            return status_map.get(status, (0, ZERO))[0]

        total_value = money(
            (await self.session.execute(select(func.coalesce(func.sum(Quotation.grand_total), 0)))).scalar_one()
        )
        approved_value = status_map.get(QuotationStatus.APPROVED, (0, ZERO))[1]
        monthly_count = (
            await self.session.execute(
                select(func.count(Quotation.id)).where(Quotation.quotation_date >= month_start)
            )
        ).scalar_one()
        monthly_value = money(
            (
                await self.session.execute(
                    select(func.coalesce(func.sum(Quotation.grand_total), 0)).where(
                        Quotation.quotation_date >= month_start
                    )
                )
            ).scalar_one()
        )
        recent = (
            await self.session.execute(
                select(Quotation)
                .options(joinedload(Quotation.customer), joinedload(Quotation.project))
                .order_by(Quotation.created_at.desc())
                .limit(8)
            )
        ).scalars().unique().all()
        customer_rows = (
            await self.session.execute(
                select(
                    Customer.id,
                    Customer.name,
                    func.count(Quotation.id),
                    func.coalesce(func.sum(Quotation.grand_total), 0),
                )
                .join(Quotation, Quotation.customer_id == Customer.id)
                .group_by(Customer.id, Customer.name)
                .order_by(func.sum(Quotation.grand_total).desc())
                .limit(10)
            )
        ).all()
        distribution = [
            StatusCount(status=status, count=vals[0], value=vals[1]) for status, vals in status_map.items()
        ]
        return DashboardSummary(
            total_quotations=total,
            draft_quotations=count_for(QuotationStatus.DRAFT),
            sent_quotations=count_for(QuotationStatus.SENT),
            approved_quotations=count_for(QuotationStatus.APPROVED),
            rejected_quotations=count_for(QuotationStatus.REJECTED),
            expired_quotations=count_for(QuotationStatus.EXPIRED),
            total_quotation_value=total_value,
            approved_quotation_value=approved_value,
            monthly_quotation_value=monthly_value,
            monthly_quotation_count=monthly_count,
            recent_quotations=[QuotationListItem.model_validate(item) for item in recent],
            quotation_status_distribution=distribution,
            customer_wise_quotation_value=[
                CustomerValue(
                    customer_id=row[0],
                    customer_name=row[1],
                    quotation_count=row[2],
                    total_value=money(row[3]),
                )
                for row in customer_rows
            ],
        )
