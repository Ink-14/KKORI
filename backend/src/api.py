from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.configs.raw_string_searcher_config import RAW_STRING_RULES
from src.configs.spell_checker_config import SPELL_CHECK_RULES
from src.engines.raw_searcher import RawStringSearcher
from src.engines.spell_checker import SpellChecker
from src.models.interface import SpellError
from src.tokenizations.ko_tokenizer import KoTokenizer

_raw_searcher: RawStringSearcher | None = None
_spell_checker: SpellChecker | None = None
_tokenizer: KoTokenizer | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _raw_searcher, _spell_checker, _tokenizer
    _raw_searcher = RawStringSearcher()
    _raw_searcher.add_word_from_list(RAW_STRING_RULES)

    _tokenizer = KoTokenizer()
    _tokenizer.tokenize("")

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
    allow_methods=["POST"],
    allow_headers=["*"],
)


class CheckRequest(BaseModel):
    text: str


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
def nfa_check(body: CheckRequest) -> list[SpellErrorResponse]:
    assert _spell_checker is not None
    assert _tokenizer is not None
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


@app.post("/check", response_model=list[SpellErrorResponse])
def check(body: CheckRequest) -> list[SpellErrorResponse]:
    assert _raw_searcher is not None
    assert _spell_checker is not None
    assert _tokenizer is not None
    raw_results: list[SpellError] = _raw_searcher.search(body.text)
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
