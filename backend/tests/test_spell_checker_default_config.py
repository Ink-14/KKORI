import csv
from pathlib import Path
from dataclasses import dataclass

import pytest

from helpers import assert_error, assert_no_errors, check_error_type
from src.engines.configs.rule import SPELL_CHECK_RULES
from src.models.interface import SpellErrorType


@dataclass
class Case:
    correct: str = ""
    wrong: str = ""
    error_type: SpellErrorType = SpellErrorType.NOT_SET
    is_pending: bool = False
    source: str = ""

FILE_ERROR_MAPPING = {
    "spacing.tsv": SpellErrorType.SPACING,
    "spelling.tsv": SpellErrorType.SPELLING,
    "complex.tsv": SpellErrorType.COMPLEX,
    "loanword.tsv": SpellErrorType.LOANWORD,
    "meaning.tsv": SpellErrorType.MEANING,
}

CURRENT_DIR = Path(__file__).parent
DATA_ROOTS = [CURRENT_DIR / "data"]
PENDING_DIR_NAME = "pending"

def load_cases_from_tsv(file_path: Path, is_pending: bool = False) -> list[Case]:
    cases = []

    if not file_path.exists():
        print(f"\n[Warning] {file_path} 파일이 없습니다. 해당 케이스를 건너뜁니다.")
        return cases

    error_type = FILE_ERROR_MAPPING.get(file_path.name, SpellErrorType.NOT_SET)
    source = str(file_path.relative_to(CURRENT_DIR))

    with open(file_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            correct_text = (row.get("correct") or "").strip()
            wrong_text = (row.get("wrong") or "").strip()

            if not correct_text and not wrong_text:
                continue

            cases.append(Case(
                correct=correct_text,
                wrong=wrong_text,
                error_type=error_type,
                is_pending=is_pending,
                source=source,
            ))

    return cases

def load_all_cases() -> list[Case]:
    cases = []
    for root in DATA_ROOTS:
        for filename in FILE_ERROR_MAPPING.keys():
            cases.extend(load_cases_from_tsv(root / filename, is_pending=False))
            cases.extend(load_cases_from_tsv(
                root / PENDING_DIR_NAME / filename, is_pending=True
            ))
    return cases

ALL_CASES = load_all_cases()

def make_param(c: Case):
    marks = []
    if c.is_pending:
        marks.append(pytest.mark.xfail(
            reason=f"pending: 아직 미구현 ({c.source})",
            strict=True,
        ))

    label = c.wrong or c.correct
    prefix = "PENDING-" if c.is_pending else ""
    return pytest.param(c, id=f"{prefix}{label}", marks=marks)

class TestSpellChecker:
    @pytest.mark.parametrize("c", [make_param(c) for c in ALL_CASES])
    def test_spell_checker_from_tsv(self, configured_checker, tokenizer, c: Case):
        __tracebackhide__ = True
        if c.correct:
            tokens = tokenizer.tokenize(c.correct)
            errors = list(configured_checker.check(tokens))
            assert_no_errors(errors, tokens)

        if c.wrong:
            tokens = tokenizer.tokenize(c.wrong)
            errors = list(configured_checker.check(tokens))
            assert_error(errors, tokens)
            if c.error_type:
                check_error_type(errors, c.error_type)