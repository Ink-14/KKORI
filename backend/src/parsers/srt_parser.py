from pathlib import Path
from typing import Iterator
import re

from src.parsers.base import Parser, ParsedText

TIMESTAMP_REGEX = re.compile("[^-]+-->.+")
    
class SrtParser(Parser):
    def __init__(self):
        pass
    
    def parse(self, file: Path) -> Iterator[ParsedText]:
        with open(file, mode="r", encoding="UTF-8") as f:
            lines = f.read().splitlines()

        timestamp_indices = [idx for idx, line in enumerate(lines) if TIMESTAMP_REGEX.match(line)]

        for i, ts_idx in enumerate(timestamp_indices):
            end = timestamp_indices[i + 1] - 2 if i + 1 < len(timestamp_indices) else len(lines)
            text_lines = lines[ts_idx + 1:end]
            while text_lines and text_lines[-1] == "":
                text_lines.pop()
            yield ParsedText(metadata=lines[ts_idx], text="\n".join(text_lines))
    
    
    