"""Spooli package.

The flat modules at the repository root stay importable during the
refactor; shared configuration lives in ``spooli.constants``, the SQLite
persistence layer in ``spooli.storage``, the business logic in
``spooli.domain`` (re-exported at the root through the ``core`` facade),
the G-code/3MF metadata engine in ``spooli.parsing``
(re-exported at the root through the ``parser`` facade),
the business workflows in ``spooli.services`` (pricing and currency
migration), the terminal user interface in ``spooli.ui``
(console styling, input primitives, table renderer) with the
interactive screens in ``spooli.ui.screens``
(re-exported at the root through the ``menu`` facade), and the
command-line interface orchestration in ``spooli.cli``
(re-exported at the root through the ``main`` facade).
"""