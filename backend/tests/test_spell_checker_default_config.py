import csv
from pathlib import Path
from dataclasses import dataclass

import pytest

from helpers import assert_error, assert_no_errors, check_error_type
from src.engines.configs.rule import SPELL_CHECK_RULES
from src.models.interface import SpellErrorType

@dataclass
class Case:
    text: str
    expect_error: bool = True
    error_type: SpellErrorType = SpellErrorType.NOT_SET

FILE_ERROR_MAPPING = {
    "spacing.tsv": SpellErrorType.SPACING,
    "spelling.tsv": SpellErrorType.SPELLING,
    "meaning.tsv": SpellErrorType.MEANING,
}

def load_cases_from_tsv(file_path: Path) -> list[Case]:
    cases = []
    
    if not file_path.exists():
        print(f"\n[Warning] {file_path.name} 파일이 없습니다. 해당 케이스를 건너뜁니다.")
        return cases

    error_type = FILE_ERROR_MAPPING.get(file_path.name, SpellErrorType.NOT_SET)
    
    with open(file_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            correct_text = (row.get("correct") or "").strip()
            wrong_text = (row.get("wrong") or "").strip()

            if correct_text:
                cases.append(Case(text=correct_text, expect_error=False))
            
            if wrong_text:
                cases.append(Case(text=wrong_text, expect_error=True, error_type=error_type))
                
    return cases

CURRENT_DIR = Path(__file__).parent
TEST_DATA_DIR = CURRENT_DIR / "data"
ALL_CASES = []

for filename in FILE_ERROR_MAPPING.keys():
    file_path = TEST_DATA_DIR / filename
    ALL_CASES.extend(load_cases_from_tsv(file_path))


class TestSpellChecker:
    @pytest.mark.parametrize(
        "c", 
        ALL_CASES, 
        ids=lambda c: f"{'ERROR' if c.expect_error else 'PASS'}-{c.text}"
    )
    def test_spell_checker_from_tsv(self, configured_checker, tokenizer, c: Case):
        tokens = tokenizer.tokenize(c.text)
        errors = list(configured_checker.check(tokens))

        if c.expect_error:
            assert_error(errors, tokens)
            if c.error_type:
                check_error_type(errors, c.error_type)
        else:
            assert_no_errors(errors, tokens)