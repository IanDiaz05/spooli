"""Spooli package.

The flat modules at the repository root stay importable during the
refactor; shared configuration lives in ``spooli.constants``, the SQLite
persistence layer in ``spooli.storage``, the business logic in
``spooli.domain`` (re-exported at the root through the ``core`` facade),
and the G-code/3MF metadata engine in ``spooli.parsing``
(re-exported at the root through the ``parser`` facade).
"""
