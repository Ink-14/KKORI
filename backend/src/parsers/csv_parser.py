from pathlib import Path
from typing import Iterator
import csv

from src.parsers.base import Parser, ParsedText

class CsvParser(Parser):
    def __init__(self, text_col: str, metadata_col: str | None = None, encoding: str = "utf-8"):
        self.text_col = text_col
        self.metadata_col = metadata_col
        self.encoding = encoding

    def parse(self, file: Path) -> Iterator[ParsedText]:
        with open(file, encoding=self.encoding, newline="") as f:
            reader = csv.DictReader(f)

            for row_num, row in enumerate(reader, start=2):
                text_val = row.get(self.text_col)
                if not text_val:
                    continue
                text = str(text_val)

                if self.metadata_col is not None:
                    meta_val = row.get(self.metadata_col)
                    metadata = str(meta_val) if meta_val is not None else ""
                else:
                    metadata = str(row_num)

                yield ParsedText(text=text, metadata=metadata)
