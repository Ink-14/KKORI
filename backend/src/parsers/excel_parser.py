from pathlib import Path
from typing import Iterator

import openpyxl

from src.parsers.base import Parser, ParsedText

def _letter_to_idx(letter: str) -> int:
    """'A' -> 0, 'B' -> 1, ... 'Z' -> 25, 'AA' -> 26 ..."""
    idx = 0
    for ch in letter:
        idx = idx * 26 + (ord(ch.upper()) - 64)
    return idx - 1

class ExcelParser(Parser):
    def __init__(self, sheet_name: str, text_col: str, metadata_col: str | None = None, has_header: bool = True):
        self.sheet_name = sheet_name
        self.text_col = text_col
        self.metadata_col = metadata_col
        self.has_header = has_header

    def _resolve_idx(self, col: str, headers: list[str]) -> int:
        if self.has_header:
            return headers.index(col)
        return _letter_to_idx(col)

    def parse(self, file: Path) -> Iterator[ParsedText]:
        wb = openpyxl.load_workbook(file, read_only=True, data_only=True)
        ws = wb[self.sheet_name]

        rows = list(ws.iter_rows(values_only=True))
        if not rows:
            wb.close()
            return

        if self.has_header:
            headers = [str(c) if c is not None else "" for c in rows[0]]
            data_rows = rows[1:]
            start = 2
        else:
            headers = []
            data_rows = rows
            start = 1

        text_idx = self._resolve_idx(self.text_col, headers)
        meta_idx = (
            self._resolve_idx(self.metadata_col, headers)
            if self.metadata_col
            else None
        )

        for row_num, row in enumerate(data_rows, start=start):
            text_val = row[text_idx] if text_idx < len(row) else None
            if text_val is None:
                continue
            text = str(text_val)

            if meta_idx is not None:
                meta_val = row[meta_idx] if meta_idx < len(row) else None
                metadata = str(meta_val) if meta_val is not None else ""
            else:
                metadata = str(row_num)

            yield ParsedText(text=text, metadata=metadata)

        wb.close()
