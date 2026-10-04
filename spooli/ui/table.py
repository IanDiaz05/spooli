"""Declarative table renderer with dynamic separators."""

from __future__ import annotations


class Table:
    """Render aligned text tables with dynamic separators."""

    def __init__(self, headers: list[str], col_widths: list[int]) -> None:
        """Store headers and their column widths."""
        self.headers = list(headers)
        self.col_widths = list(col_widths)

    def header_line(self) -> str:
        """Build the header line padded to the column widths."""
        cells = [
            f"{str(header):<{width}}"
            for header, width in zip(self.headers, self.col_widths)
        ]
        return " ".join(cells).rstrip()

    def separator(self) -> str:
        """Build a separator matching the header line width."""
        return "-" * len(self.header_line())

    def format_row(self, cells: list[str]) -> str:
        """Format a single row padded to the column widths."""
        parts = [
            f"{str(cell):<{width}}"
            for cell, width in zip(cells, self.col_widths)
        ]
        return " ".join(parts).rstrip()

    def render(self, rows: list[list[str]]) -> str:
        """Render the full table including separators."""
        lines = [self.header_line(), self.separator()]
        for row in rows:
            lines.append(self.format_row(row))
        return "\n".join(lines)


def render_table(
    headers: list[str], rows: list[list[str]], col_widths: list[int]
) -> str:
    """Render headers and rows as an aligned text table."""
    return Table(headers, col_widths).render(rows)


__all__ = ["Table", "render_table"]
