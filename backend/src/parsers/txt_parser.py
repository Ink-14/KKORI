from pathlib import Path
from typing import Iterator

from src.parsers.base import Parser, ParsedText

class TxtParser(Parser):
    def __init__(self):
        pass
    
    def parse(self, file: Path) -> Iterator[ParsedText]:
        with open(file, mode="r", encoding="UTF-8") as f:
            lines = f.read().splitlines()

        for idx, line in enumerate(lines):
            yield ParsedText(metadata=str(idx), text=line)