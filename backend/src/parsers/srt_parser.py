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
        
        last_seen_timestamp = 0
        
        for idx, line in enumerate(lines):
            if TIMESTAMP_REGEX.match(line):
                if last_seen_timestamp > 0:
                    yield ParsedText(metadata=lines[last_seen_timestamp], text="\n".join(lines[last_seen_timestamp+1:idx-2]))
                last_seen_timestamp = idx
        yield ParsedText(metadata=lines[last_seen_timestamp], text="\n".join(lines[last_seen_timestamp+1:idx]))
    
    
    