import asyncio
import json
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from src.configs.raw_string_searcher_config import RAW_STRING_RULES
from src.configs.spell_checker_config import SPELL_CHECK_RULES
from src.engines.raw_searcher import RawStringSearcher
from src.engines.spell_checker import SpellChecker
from src.models.interface import SpellError, Tag
from src.tokenizations.ko_tokenizer import KoTokenizer

_raw_searcher: RawStringSearcher | None = None
_spell_checker: SpellChecker | None = None
_tokenizer: KoTokenizer | None = None
_tokenizer_lock: asyncio.Lock | None = None

_USER_WORDS_PATH = Path(__file__).parent.parent / "data" / "user_words.json"


def _load_user_words() -> list[dict]:
    if not _USER_WORDS_PATH.exists():
        return []
    with open(_USER_WORDS_PATH, encoding="utf-8") as f:
        return json.load(f)


def _save_user_words(words: list[dict]) -> None:
    _USER_WORDS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(_USER_WORDS_PATH, "w", encoding="utf-8") as f:
        json.dump(words, f, ensure_ascii=False, indent=2)


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _raw_searcher, _spell_checker, _tokenizer, _tokenizer_lock
    _tokenizer_lock = asyncio.Lock()

    _raw_searcher = RawStringSearcher()
    _raw_searcher.add_word_from_list(RAW_STRING_RULES)

    _tokenizer = KoTokenizer()
    _tokenizer.tokenize("")
    for entry in _load_user_words():
        _tokenizer.add_user_word(entry["word"], Tag[entry["tag"]])

    _spell_checker = SpellChecker()
    _spell_checker.add_rule_from_list(SPELL_CHECK_RULES)
    yield


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://ink-14.github.io",
    ],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

class CheckRequest(BaseModel):
    text: str


class WordEntry(BaseModel):
    word: str
    tag: str


class AddWordsRequest(BaseModel):
    words: list[WordEntry]


class SpellErrorResponse(BaseModel):
    error_type: str
    error_message: str
    start_index: int
    end_index: int
    rule_id: str


@app.post("/raw-check", response_model=list[SpellErrorResponse])
def raw_check(body: CheckRequest) -> list[SpellErrorResponse]:
    assert _raw_searcher is not None
    results: list[SpellError] = _raw_searcher.search(body.text)
    return [
        SpellErrorResponse(
            error_type=e.error_type.name,
            error_message=e.error_message,
            start_index=e.start_index,
            end_index=e.end_index,
            rule_id=e.rule_id,
        )
        for e in results
    ]

@app.post("/nfa-check", response_model=list[SpellErrorResponse])
async def nfa_check(body: CheckRequest) -> list[SpellErrorResponse]:
    assert _spell_checker is not None
    assert _tokenizer is not None
    assert _tokenizer_lock is not None
    async with _tokenizer_lock:
        tokens = _tokenizer.tokenize(body.text)
    results = list(_spell_checker.check(tokens))
    return [
        SpellErrorResponse(
            error_type=e.error_type.name,
            error_message=e.error_message,
            start_index=e.start_index,
            end_index=e.end_index,
            rule_id=e.rule_id,
        )
        for e in results
    ]


@app.get("/words")
def get_words() -> list[dict]:
    return _load_user_words()


def _apply_user_words_to_tokenizer(words: list[dict], score: float = 0.0) -> None:
    global _tokenizer
    _tokenizer = KoTokenizer.reset()
    for entry in words:
        _tokenizer.add_user_word(entry["word"], Tag[entry["tag"]], score)


@app.post("/add-words", status_code=200)
async def add_words(body: AddWordsRequest):
    assert _tokenizer_lock is not None
    async with _tokenizer_lock:
        updated = [e.model_dump() for e in body.words]
        _save_user_words(updated)
        _apply_user_words_to_tokenizer(updated)
    return {"saved": len(updated)}


@app.post("/check", response_model=list[SpellErrorResponse])
async def check(body: CheckRequest) -> list[SpellErrorResponse]:
    assert _raw_searcher is not None
    assert _spell_checker is not None
    assert _tokenizer is not None
    assert _tokenizer_lock is not None
    raw_results: list[SpellError] = _raw_searcher.search(body.text)
    async with _tokenizer_lock:
        tokens = _tokenizer.tokenize(body.text)
    nfa_results = list(_spell_checker.check(tokens))
    return [
        SpellErrorResponse(
            error_type=e.error_type.name,
            error_message=e.error_message,
            start_index=e.start_index,
            end_index=e.end_index,
            rule_id=e.rule_id,
        )
        for e in [*raw_results, *nfa_results]
    ]


_FRONTEND_DIST = Path(__file__).parent.parent.parent / "frontend" / "dist"
if _FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=_FRONTEND_DIST / "assets"), name="assets")

    @app.get("/")
    def serve_index():
        return FileResponse(_FRONTEND_DIST / "index.html")

    @app.get("/{full_path:path}")
    def serve_spa(full_path: str):
        file = _FRONTEND_DIST / full_path
        if file.exists() and file.is_file():
            return FileResponse(file)
        return FileResponse(_FRONTEND_DIST / "index.html")
