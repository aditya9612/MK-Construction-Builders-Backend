"""Enums and constants for website CMS models (separate from ERP enums)."""

from enum import StrEnum


class MediaFolder(StrEnum):
    """Allowed upload folders for website media."""

    PROJECTS = "projects"
    GALLERY = "gallery"
    SERVICES = "services"
    COMPANY = "company"
    REVIEWS = "reviews"


class PublicationStatus(StrEnum):
    """Publication state for public website content."""

    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"


class PortfolioProjectType(StrEnum):
    """Display type for portfolio projects on the website."""

    RESIDENTIAL = "RESIDENTIAL"
    COMMERCIAL = "COMMERCIAL"
    INDUSTRIAL = "INDUSTRIAL"
    RENOVATION = "RENOVATION"
    OTHER = "OTHER"


class PortfolioDisplayStatus(StrEnum):
    """Public-facing construction status for portfolio projects (not ERP ProjectStatus)."""

    PLANNED = "PLANNED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    SHOWCASE = "SHOWCASE"


class GalleryCategory(StrEnum):
    """Gallery item categories for website filtering."""

    PROJECTS = "projects"
    SITE = "site"
    INTERIOR = "interior"
    EXTERIOR = "exterior"
    TEAM = "team"
    OTHER = "other"
