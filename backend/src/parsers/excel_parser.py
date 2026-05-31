from pathlib import Path
from typing import Iterator

import openpyxl

from src.parsers.base import Parser, ParsedText

class ExcelParser(Parser):
    def __init__(self, sheet_name: str, text_col: str, metadata_col: str | None = None):
        self.sheet_name = sheet_name
        self.text_col = text_col
        self.metadata_col = metadata_col

    def parse(self, file: Path) -> Iterator[ParsedText]:
        wb = openpyxl.load_workbook(file, read_only=True, data_only=True)
        ws = wb[self.sheet_name]

        rows = list(ws.iter_rows(values_only=True))
        if not rows:
            wb.close()
            return

        headers = [str(c) if c is not None else "" for c in rows[0]]

        text_idx = headers.index(self.text_col)
        meta_idx = headers.index(self.metadata_col) if self.metadata_col else None

        for row_num, row in enumerate(rows[1:], start=2):
            text_val = row[text_idx]
            if text_val is None:
                continue
            text = str(text_val)

            if meta_idx is not None:
                meta_val = row[meta_idx]
                metadata = str(meta_val) if meta_val is not None else ""
            else:
                metadata = str(row_num)

            yield ParsedText(text=text, metadata=metadata)

        wb.close()
