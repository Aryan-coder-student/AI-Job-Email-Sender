from __future__ import annotations

from app.core.exceptions.base import AppError


class InvalidExcelError(AppError):
    """Raised when an Excel file cannot be downloaded, opened, or parsed."""


class InvalidResumeError(AppError):
    """Raised when a resume file cannot be validated, opened, or parsed."""


class InvalidGitHubError(AppError):
    """Raised when GitHub URL/username is invalid or API fetch fails."""
