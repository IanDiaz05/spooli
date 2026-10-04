"""Typed domain errors of Spooli."""

from __future__ import annotations


class SpooliError(Exception):
    """Base error of Spooli."""


class DomainError(SpooliError, ValueError):
    """Base domain error.

    Inherits from ValueError for backwards compatibility with
    legacy callers catching ValueError.
    """


class NoCompatibleSpoolError(DomainError):
    """No spool of the requested material holds enough filament."""


class InsufficientFilamentError(DomainError):
    """A manually selected spool holds insufficient filament."""


class SpoolNotFoundError(DomainError):
    """A manually selected spool identifier does not exist."""


class UnsupportedFormatError(DomainError):
    """A file extension is not supported by the parsing engine."""


class MissingMetadataError(DomainError):
    """Required slicer metadata is absent from a parsed file."""
