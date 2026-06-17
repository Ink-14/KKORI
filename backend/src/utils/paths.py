import sys
from pathlib import Path


def _meipass() -> Path | None:
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS)  # type: ignore
    return None

def backend_resource_path(*parts: str) -> Path:
    base = _meipass() or Path(__file__).parent.parent.parent
    return base.joinpath(*parts)

def frontend_dist_path() -> Path:
    if meipass := _meipass():
        return meipass / "frontend" / "dist" / "desktop"
    return Path(__file__).parent.parent.parent.parent / "frontend" / "dist" / "desktop"

def user_data_path(*parts: str) -> Path:
    base = Path.home() / "AppData" / "Roaming" / "KoreanSpellChecker"
    path = base.joinpath(*parts)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path
