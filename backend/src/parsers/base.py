from typing import Iterator
from abc import ABC, abstractmethod
from pathlib import Path
from dataclasses import dataclass

@dataclass
class ParsedText:
    text: str
    metadata: str
    
class Parser(ABC):
    @abstractmethod
    def parse(self, file: Path) -> Iterator[ParsedText]:
        raise NotImplementedError("'parse' method must be implemented.")