"""Customer feedback and Google reviews routes.

Public endpoints are unauthenticated and return only published feedback.
Admin endpoints require administrative authorization and manage feedback records and media.
"""

from __future__ import annotations

from datetime import date
from typing import Any

from fastapi import (
    APIRouter,
    Body,
    Depends,
    File,
    Query,
    Request,
    Response,
    UploadFile,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_admin
from app.core.database import get_db
from app.core.exceptions import ValidationFailedError
from app.models.customer_feedback import ReviewSource
from app.models.user import User
from app.schemas.common import PaginatedData, SuccessResponse
from app.schemas.customer_feedback import (
    CustomerFeedbackAdminStatisticsResponse,
    CustomerFeedbackCreate,
    CustomerFeedbackPublicResponse,
    CustomerFeedbackPublicStatisticsResponse,
    CustomerFeedbackResponse,
    CustomerFeedbackUpdate,
    FeedbackDisplayOrderUpdate,
    FeedbackFeaturedUpdate,
    FeedbackPublishUpdate,
    PhotoUploadResponse,
)
from app.services.customer_feedback_service import CustomerFeedbackService

router = APIRouter(prefix="/customer-feedback", tags=["Customer Feedback"])


# ==============================================================================
# Public APIs (Unauthenticated)
# ==============================================================================


@router.get(
    "/public/statistics",
    response_model=SuccessResponse[CustomerFeedbackPublicStatisticsResponse],
    summary="Get public customer feedback statistics",
)
async def get_public_statistics(
    db: AsyncSession = Depends(get_db),
):
    stats = await CustomerFeedbackService(db).get_public_statistics()
    return SuccessResponse(data=stats)


@router.get(
    "/public",
    response_model=SuccessResponse[PaginatedData[CustomerFeedbackPublicResponse]],
    summary="List published customer feedback",
)
async def list_public_feedback(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    rating: int | None = Query(None, ge=1, le=5, description="Filter by rating (1-5)"),
    review_source: ReviewSource | None = Query(
        None, description="Filter by review source (google, website, manual)"
    ),
    is_featured: bool | None = Query(None, description="Filter by featured status"),
    sort_by: str = Query("display_order", description="Sort field"),
    sort_order: str = Query("asc", description="Sort direction (asc/desc)"),
    db: AsyncSession = Depends(get_db),
):
    source_val = review_source.value if review_source else None
    data = await CustomerFeedbackService(db).list_public(
        page=page,
        page_size=page_size,
        rating=rating,
        review_source=source_val,
        is_featured=is_featured,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    return SuccessResponse(data=data)


@router.get(
    "/public/{feedback_id}",
    response_model=SuccessResponse[CustomerFeedbackPublicResponse],
    summary="Get published customer feedback by ID",
)
async def get_public_feedback(
    feedback_id: int,
    db: AsyncSession = Depends(get_db),
):
    data = await CustomerFeedbackService(db).get_public(feedback_id)
    return SuccessResponse(data=data)


# ==============================================================================
# Admin APIs (Authentication Required)
# ==============================================================================


@router.get(
    "/admin/statistics",
    response_model=SuccessResponse[CustomerFeedbackAdminStatisticsResponse],
    summary="Get administrative customer feedback statistics",
)
async def get_admin_statistics(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    stats = await CustomerFeedbackService(db).get_admin_statistics()
    return SuccessResponse(data=stats)


@router.post(
    "/upload-photo",
    response_model=SuccessResponse[PhotoUploadResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Upload customer profile photo",
)
async def upload_feedback_photo(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    uploaded = await CustomerFeedbackService(db).upload_photo(file)
    return SuccessResponse(
        message="Customer photo uploaded successfully",
        data=uploaded,
    )


@router.post(
    "/{feedback_id}/photo",
    response_model=SuccessResponse[CustomerFeedbackResponse],
    summary="Attach customer profile photo to feedback",
)
async def attach_feedback_photo(
    feedback_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    data = await CustomerFeedbackService(db).attach_photo(feedback_id, file)
    return SuccessResponse(
        message="Photo attached to customer feedback successfully",
        data=data,
    )


@router.patch(
    "/{feedback_id}/publish",
    response_model=SuccessResponse[CustomerFeedbackResponse],
    summary="Publish or unpublish customer feedback",
)
async def set_publish_status(
    feedback_id: int,
    payload: FeedbackPublishUpdate | None = None,
    is_published: bool | None = Query(None, description="Direct query parameter alternative"),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    target_status = payload.is_published if payload is not None else is_published
    if target_status is None:
        raise ValidationFailedError("is_published status must be provided in body or query")
    data = await CustomerFeedbackService(db).set_publish_status(feedback_id, target_status)
    return SuccessResponse(
        message=f"Feedback {'published' if target_status else 'unpublished'} successfully",
        data=data,
    )


@router.patch(
    "/{feedback_id}/featured",
    response_model=SuccessResponse[CustomerFeedbackResponse],
    summary="Mark or unmark featured customer feedback",
)
async def set_featured_status(
    feedback_id: int,
    payload: FeedbackFeaturedUpdate | None = None,
    is_featured: bool | None = Query(None, description="Direct query parameter alternative"),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    target_status = payload.is_featured if payload is not None else is_featured
    if target_status is None:
        raise ValidationFailedError("is_featured status must be provided in body or query")
    data = await CustomerFeedbackService(db).set_featured_status(feedback_id, target_status)
    return SuccessResponse(
        message=f"Feedback {'marked as featured' if target_status else 'unmarked as featured'} successfully",
        data=data,
    )


@router.patch(
    "/{feedback_id}/display-order",
    response_model=SuccessResponse[CustomerFeedbackResponse],
    summary="Update customer feedback display sequence",
)
async def set_display_order(
    feedback_id: int,
    payload: FeedbackDisplayOrderUpdate | None = None,
    display_order: int | None = Query(
        None, ge=0, description="Direct query parameter alternative"
    ),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    target_order = payload.display_order if payload is not None else display_order
    if target_order is None:
        raise ValidationFailedError("display_order must be provided in body or query")
    data = await CustomerFeedbackService(db).set_display_order(feedback_id, target_order)
    return SuccessResponse(
        message="Display order updated successfully",
        data=data,
    )


@router.post(
    "",
    response_model=SuccessResponse[CustomerFeedbackResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create new customer feedback",
)
async def create_feedback(
    request: Request,
    payload: CustomerFeedbackCreate | None = Body(None),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    service = CustomerFeedbackService(db)
    content_type = request.headers.get("content-type", "")

    if "multipart/form-data" in content_type:
        form = await request.form()
        uploaded_file = form.get("customer_photo") or form.get("photo") or form.get("file")
        photo_url = None
        if uploaded_file and hasattr(uploaded_file, "filename") and uploaded_file.filename:
            uploaded = await service.upload_photo(uploaded_file)
            photo_url = uploaded.url_path
        elif isinstance(form.get("customer_photo"), str):
            photo_url = form.get("customer_photo") or None

        raw_rating = form.get("rating")
        try:
            rating_val = int(raw_rating) if raw_rating is not None else 5
        except (ValueError, TypeError):
            raise ValidationFailedError("Rating must be an integer between 1 and 5")

        raw_display_order = form.get("display_order")
        try:
            display_order_val = int(raw_display_order) if raw_display_order is not None else 0
        except (ValueError, TypeError):
            display_order_val = 0

        raw_date = form.get("review_date")
        parsed_date = None
        if raw_date:
            try:
                parsed_date = date.fromisoformat(str(raw_date))
            except ValueError:
                raise ValidationFailedError("Invalid review_date format, expected YYYY-MM-DD")

        raw_source = form.get("review_source", "website")
        try:
            review_source_enum = ReviewSource(str(raw_source).lower())
        except ValueError:
            raise ValidationFailedError("Invalid review_source. Must be 'google', 'website', or 'manual'")

        create_data = CustomerFeedbackCreate(
            customer_name=str(form.get("customer_name") or ""),
            customer_location=str(form.get("customer_location") or ""),
            customer_photo=photo_url,
            rating=rating_val,
            review_title=form.get("review_title"),
            review_message=str(form.get("review_message") or ""),
            project_name=form.get("project_name"),
            review_source=review_source_enum,
            google_review_url=form.get("google_review_url"),
            review_date=parsed_date,
            is_featured=str(form.get("is_featured", "")).lower() in ("true", "1", "yes"),
            is_published=str(form.get("is_published", "")).lower() in ("true", "1", "yes"),
            display_order=display_order_val,
        )
        data = await service.create(create_data)
        return SuccessResponse(message="Customer feedback created successfully", data=data)

    if payload is None:
        try:
            body = await request.json()
            payload = CustomerFeedbackCreate.model_validate(body)
        except Exception as exc:
            raise ValidationFailedError("Valid JSON request body is required") from exc

    data = await service.create(payload)
    return SuccessResponse(message="Customer feedback created successfully", data=data)


@router.get(
    "",
    response_model=SuccessResponse[PaginatedData[CustomerFeedbackResponse]],
    summary="List all customer feedback (admin)",
)
async def list_admin_feedback(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    search: str | None = Query(None, description="Search name, location, message, project"),
    rating: int | None = Query(None, ge=1, le=5, description="Filter by rating (1-5)"),
    review_source: ReviewSource | None = Query(
        None, description="Filter by review source (google, website, manual)"
    ),
    is_published: bool | None = Query(None, description="Filter by publication status"),
    is_featured: bool | None = Query(None, description="Filter by featured status"),
    sort_by: str = Query("display_order", description="Sort field"),
    sort_order: str = Query("asc", description="Sort direction (asc/desc)"),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    source_val = review_source.value if review_source else None
    data = await CustomerFeedbackService(db).list_admin(
        page=page,
        page_size=page_size,
        search=search,
        rating=rating,
        review_source=source_val,
        is_published=is_published,
        is_featured=is_featured,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    return SuccessResponse(data=data)


@router.get(
    "/{feedback_id}",
    response_model=SuccessResponse[CustomerFeedbackResponse],
    summary="Get complete feedback details (admin)",
)
async def get_admin_feedback(
    feedback_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    data = await CustomerFeedbackService(db).get_admin(feedback_id)
    return SuccessResponse(data=data)


@router.put(
    "/{feedback_id}",
    response_model=SuccessResponse[CustomerFeedbackResponse],
    summary="Update existing customer feedback",
)
async def update_feedback(
    feedback_id: int,
    payload: CustomerFeedbackUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    data = await CustomerFeedbackService(db).update(feedback_id, payload)
    return SuccessResponse(message="Customer feedback updated successfully", data=data)


@router.delete(
    "/{feedback_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete customer feedback safely",
)
async def delete_feedback(
    feedback_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    await CustomerFeedbackService(db).delete(feedback_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
