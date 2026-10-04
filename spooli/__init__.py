"""Spooli package.

The flat modules at the repository root stay importable during the
refactor; shared configuration lives in ``spooli.constants``, the SQLite
persistence layer in ``spooli.storage``, and the business logic in
``spooli.domain`` (re-exported at the root through the ``core`` facade).
"""
