from fastapi import APIRouter

from app.api.routes import (
    auth,
    customers,
    dashboard,
    doors_windows,
    electrical,
    materials,
    painting,
    plumbing,
    projects,
    quotations,
    rates,
    reports,
    settings,
    terms,
    tiles_granite,
)

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(customers.router)
api_router.include_router(projects.router)
api_router.include_router(quotations.router)
api_router.include_router(rates.router)
api_router.include_router(materials.router)
api_router.include_router(electrical.router)
api_router.include_router(plumbing.router)
api_router.include_router(doors_windows.router)
api_router.include_router(tiles_granite.router)
api_router.include_router(painting.router)
api_router.include_router(terms.router)
api_router.include_router(settings.router)
api_router.include_router(dashboard.router)
api_router.include_router(reports.router)
