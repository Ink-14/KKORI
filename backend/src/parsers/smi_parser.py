from pathlib import Path
from typing import Iterator
import html
import re

from src.parsers.base import Parser, ParsedText

SYNC_REGEX = re.compile(r"<SYNC\b[^>]*?\bStart\s*=\s*[\"']?(\d+)[^>]*>", re.IGNORECASE)
BR_REGEX = re.compile(r"<br\s*/?>", re.IGNORECASE)
TAG_REGEX = re.compile(r"<[^>]+>")
ENCODINGS = ("utf-8-sig", "cp949", "utf-16")


class SmiParser(Parser):
    def __init__(self):
        pass

    def parse(self, file: Path) -> Iterator[ParsedText]:
        content = self._read(file)
        syncs = list(SYNC_REGEX.finditer(content))

        for i, sync in enumerate(syncs):
            next_sync = syncs[i + 1] if i + 1 < len(syncs) else None
            body_end = next_sync.start() if next_sync else len(content)

            text = self._clean(content[sync.end():body_end])
            if not text:
                continue

            metadata = self._format_ms(int(sync.group(1)))
            if next_sync:
                metadata += f" --> {self._format_ms(int(next_sync.group(1)))}"
            yield ParsedText(metadata=metadata, text=text)

    @staticmethod
    def _read(file: Path) -> str:
        raw = file.read_bytes()
        for encoding in ENCODINGS:
            try:
                return raw.decode(encoding)
            except UnicodeError:
                continue
        return raw.decode("utf-8", errors="replace")

    @staticmethod
    def _clean(body: str) -> str:
        body = " ".join(body.splitlines())
        body = BR_REGEX.sub("\n", body)
        body = TAG_REGEX.sub("", body)
        body = html.unescape(body).replace("\xa0", " ")
        lines = [line.strip() for line in body.split("\n")]
        return "\n".join(lines).strip()

    @staticmethod
    def _format_ms(ms: int) -> str:
        hours, rest = divmod(ms, 3_600_000)
        minutes, rest = divmod(rest, 60_000)
        seconds, millis = divmod(rest, 1000)
        return f"{hours:02}:{minutes:02}:{seconds:02},{millis:03}"