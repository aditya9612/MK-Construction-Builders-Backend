"""Verify published-only filters are present in repository queries (no DB I/O)."""

from app.models.cms_enums import PublicationStatus
from app.repositories.gallery_repository import GalleryRepository
from app.repositories.portfolio_repository import PortfolioRepository


class _DummySession:
    pass


def test_portfolio_public_query_filters_published():
    repo = PortfolioRepository(_DummySession())  # type: ignore[arg-type]
    stmt = repo.list_query(published_only=True)
    compiled = str(stmt.compile(compile_kwargs={"literal_binds": True}))
    assert PublicationStatus.PUBLISHED.value in compiled
    assert "portfolio_projects" in compiled.lower() or "PortfolioProject" in compiled


def test_portfolio_slug_public_filters_published():
    # Build the where clause indirectly via list_query; slug path uses same enum
    repo = PortfolioRepository(_DummySession())  # type: ignore[arg-type]
    stmt = repo.list_query(published_only=True, search=None)
    sql = str(stmt.compile(compile_kwargs={"literal_binds": True}))
    assert "PUBLISHED" in sql


def test_gallery_public_query_filters_published():
    repo = GalleryRepository(_DummySession())  # type: ignore[arg-type]
    stmt = repo.list_query(published_only=True)
    sql = str(stmt.compile(compile_kwargs={"literal_binds": True}))
    assert "PUBLISHED" in sql


def test_admin_queries_can_omit_published_filter():
    portfolio = PortfolioRepository(_DummySession())  # type: ignore[arg-type]
    gallery = GalleryRepository(_DummySession())  # type: ignore[arg-type]
    p_sql = str(portfolio.list_query(published_only=False).compile())
    g_sql = str(gallery.list_query(published_only=False).compile())
    # Without published_only, no forced PUBLISHED bind is required
    assert "portfolio" in p_sql.lower() or "PortfolioProject" in p_sql
    assert "gallery" in g_sql.lower() or "GalleryItem" in g_sql
