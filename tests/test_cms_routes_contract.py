"""Route contract tests: paths and auth wiring without DB mutations.

Routers are mounted on an isolated FastAPI app (not production ``app.main``)
because CMS routers are not registered until integration approval.

FastAPI >=0.143 may store included routers lazily; OpenAPI / router.routes
are used instead of flattened ``app.routes`` APIRoute objects.
"""

from fastapi import FastAPI
from fastapi.routing import APIRoute

from app.api.routes import gallery as gallery_routes
from app.api.routes import portfolio as portfolio_routes
from app.api.routes import upload as upload_routes


def _mount_cms(app: FastAPI) -> FastAPI:
    app.include_router(upload_routes.router, prefix="/api/v1")
    for router in portfolio_routes.routers:
        app.include_router(router, prefix="/api/v1")
    for router in gallery_routes.routers:
        app.include_router(router, prefix="/api/v1")
    return app


def _openapi_paths(app: FastAPI) -> set[str]:
    return set(app.openapi()["paths"].keys())


def _dep_names(route: APIRoute) -> set[str]:
    return {getattr(dep.call, "__name__", "") for dep in route.dependant.dependencies}


def test_cms_route_paths_match_spec():
    app = _mount_cms(FastAPI())
    paths = _openapi_paths(app)
    expected = {
        "/api/v1/admin/upload/image",
        "/api/v1/admin/upload/images",
        "/api/v1/admin/upload/{file_id}",
        "/api/v1/portfolio/projects",
        "/api/v1/portfolio/projects/{slug}",
        "/api/v1/admin/portfolio/projects",
        "/api/v1/admin/portfolio/projects/{project_id}",
        "/api/v1/admin/portfolio/projects/{project_id}/gallery",
        "/api/v1/gallery",
        "/api/v1/admin/gallery",
        "/api/v1/admin/gallery/{item_id}",
    }
    missing = expected - paths
    assert not missing, f"Missing CMS paths: {missing}"


def test_public_portfolio_and_gallery_have_no_auth_dependency():
    public_routes = [
        r
        for r in list(portfolio_routes.public_router.routes) + list(gallery_routes.public_router.routes)
        if isinstance(r, APIRoute)
    ]
    assert public_routes
    for route in public_routes:
        names = _dep_names(route)
        assert "require_masters" not in names
        assert "require_admin" not in names
        assert "get_current_user" not in names
        assert "require_write" not in names


def test_upload_routes_require_admin():
    checked = 0
    for route in upload_routes.router.routes:
        if not isinstance(route, APIRoute):
            continue
        if route.methods and route.methods.intersection({"POST", "PUT", "DELETE"}):
            names = _dep_names(route)
            assert "require_admin" in names, f"{route.path} missing require_admin"
            assert "require_masters" not in names, f"{route.path} must not allow managers/viewers"
            checked += 1
    assert checked >= 3


def test_admin_routes_require_masters():
    admin_route_lists = [
        portfolio_routes.admin_router.routes,
        gallery_routes.admin_router.routes,
    ]
    checked = 0
    for routes in admin_route_lists:
        for route in routes:
            if not isinstance(route, APIRoute):
                continue
            if route.methods and route.methods.intersection({"POST", "PUT", "DELETE", "GET"}):
                names = _dep_names(route)
                assert "require_masters" in names, f"{route.path} missing require_masters"
                checked += 1
    assert checked >= 8


def test_production_app_exposes_cms_routes():
    """Verify main app successfully exposes integrated CMS endpoints."""
    from app.main import app

    paths = set(app.openapi()["paths"].keys())
    assert "/api/v1/portfolio/projects" in paths
    assert "/api/v1/gallery" in paths
    assert "/api/v1/admin/upload/image" in paths

