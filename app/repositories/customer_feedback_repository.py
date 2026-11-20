"""Repository for customer feedback and Google reviews."""

from __future__ import annotations

from sqlalchemy import Select, case, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.customer_feedback import CustomerFeedback, ReviewSource

ALLOWED_FEEDBACK_SORT_FIELDS = frozenset(
    {"display_order", "rating", "review_date", "created_at", "updated_at", "id", "customer_name"}
)


class CustomerFeedbackRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, feedback_id: int) -> CustomerFeedback | None:
        return await self.session.get(CustomerFeedback, feedback_id)

    async def get_published(self, feedback_id: int) -> CustomerFeedback | None:
        stmt = select(CustomerFeedback).where(
            CustomerFeedback.id == feedback_id,
            CustomerFeedback.is_published.is_(True),
        )
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def add(self, item: CustomerFeedback) -> CustomerFeedback:
        self.session.add(item)
        await self.session.flush()
        return item

    async def delete(self, item: CustomerFeedback) -> None:
        await self.session.delete(item)

    def list_query(
        self,
        *,
        search: str | None = None,
        rating: int | None = None,
        review_source: str | None = None,
        is_published: bool | None = None,
        is_featured: bool | None = None,
        published_only: bool = False,
        sort_by: str = "display_order",
        sort_order: str = "asc",
    ) -> Select:
        stmt = select(CustomerFeedback)

        if published_only:
            stmt = stmt.where(CustomerFeedback.is_published.is_(True))
        elif is_published is not None:
            stmt = stmt.where(CustomerFeedback.is_published.is_(is_published))

        if rating is not None:
            stmt = stmt.where(CustomerFeedback.rating == rating)

        if review_source:
            stmt = stmt.where(CustomerFeedback.review_source == review_source.lower())

        if is_featured is not None:
            stmt = stmt.where(CustomerFeedback.is_featured.is_(is_featured))

        if search:
            like = f"%{search.strip()}%"
            stmt = stmt.where(
                or_(
                    CustomerFeedback.customer_name.ilike(like),
                    CustomerFeedback.customer_location.ilike(like),
                    CustomerFeedback.review_title.ilike(like),
                    CustomerFeedback.review_message.ilike(like),
                    CustomerFeedback.project_name.ilike(like),
                )
            )

        safe_sort_by = (
            sort_by if sort_by in ALLOWED_FEEDBACK_SORT_FIELDS else "display_order"
        )
        safe_sort_order = "asc" if str(sort_order).lower() == "asc" else "desc"

        if safe_sort_by == "display_order":
            primary = CustomerFeedback.display_order
            secondary = CustomerFeedback.created_at.desc()
            stmt = stmt.order_by(
                primary.asc() if safe_sort_order == "asc" else primary.desc(),
                secondary,
            )
        else:
            column = getattr(CustomerFeedback, safe_sort_by, CustomerFeedback.created_at)
            stmt = stmt.order_by(column.asc() if safe_sort_order == "asc" else column.desc())

        return stmt

    async def get_public_statistics(self) -> dict:
        stmt = select(
            func.count().label("total_published"),
            func.coalesce(func.avg(CustomerFeedback.rating), 0.0).label("avg_rating"),
            func.count(case((CustomerFeedback.rating == 1, 1))).label("star_1"),
            func.count(case((CustomerFeedback.rating == 2, 1))).label("star_2"),
            func.count(case((CustomerFeedback.rating == 3, 1))).label("star_3"),
            func.count(case((CustomerFeedback.rating == 4, 1))).label("star_4"),
            func.count(case((CustomerFeedback.rating == 5, 1))).label("star_5"),
            func.count(
                case((CustomerFeedback.review_source == ReviewSource.GOOGLE.value, 1))
            ).label("total_google"),
            func.count(
                case((CustomerFeedback.review_source == ReviewSource.WEBSITE.value, 1))
            ).label("total_website"),
        ).where(CustomerFeedback.is_published.is_(True))

        row = (await self.session.execute(stmt)).one()
        return {
            "total_published_reviews": int(row.total_published or 0),
            "average_rating": round(float(row.avg_rating or 0.0), 2),
            "rating_distribution": {
                "1": int(row.star_1 or 0),
                "2": int(row.star_2 or 0),
                "3": int(row.star_3 or 0),
                "4": int(row.star_4 or 0),
                "5": int(row.star_5 or 0),
            },
            "total_google_reviews": int(row.total_google or 0),
            "total_website_reviews": int(row.total_website or 0),
        }

    async def get_admin_statistics(self) -> dict:
        stmt = select(
            func.count().label("total_reviews"),
            func.count(case((CustomerFeedback.is_published.is_(True), 1))).label(
                "published_reviews"
            ),
            func.count(case((CustomerFeedback.is_published.is_(False), 1))).label(
                "pending_reviews"
            ),
            func.count(case((CustomerFeedback.is_featured.is_(True), 1))).label(
                "featured_reviews"
            ),
            func.coalesce(func.avg(CustomerFeedback.rating), 0.0).label("avg_rating"),
            func.count(
                case((CustomerFeedback.review_source == ReviewSource.GOOGLE.value, 1))
            ).label("google_reviews"),
            func.count(
                case((CustomerFeedback.review_source == ReviewSource.WEBSITE.value, 1))
            ).label("website_reviews"),
            func.count(
                case((CustomerFeedback.review_source == ReviewSource.MANUAL.value, 1))
            ).label("manual_reviews"),
            func.count(case((CustomerFeedback.rating == 1, 1))).label("star_1"),
            func.count(case((CustomerFeedback.rating == 2, 1))).label("star_2"),
            func.count(case((CustomerFeedback.rating == 3, 1))).label("star_3"),
            func.count(case((CustomerFeedback.rating == 4, 1))).label("star_4"),
            func.count(case((CustomerFeedback.rating == 5, 1))).label("star_5"),
        )

        row = (await self.session.execute(stmt)).one()
        return {
            "total_reviews": int(row.total_reviews or 0),
            "published_reviews": int(row.published_reviews or 0),
            "pending_reviews": int(row.pending_reviews or 0),
            "featured_reviews": int(row.featured_reviews or 0),
            "average_rating": round(float(row.avg_rating or 0.0), 2),
            "google_review_count": int(row.google_reviews or 0),
            "website_review_count": int(row.website_reviews or 0),
            "manual_review_count": int(row.manual_reviews or 0),
            "rating_distribution": {
                "1": int(row.star_1 or 0),
                "2": int(row.star_2 or 0),
                "3": int(row.star_3 or 0),
                "4": int(row.star_4 or 0),
                "5": int(row.star_5 or 0),
            },
        }
