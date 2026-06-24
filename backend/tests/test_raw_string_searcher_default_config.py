import csv
from pathlib import Path
from dataclasses import dataclass

import pytest

from helpers import assert_error_raw_text, assert_no_errors_raw_text, check_error_type
from src.engines.configs.raw_string_searcher_config import RAW_STRING_RULES
from src.models.interface import SpellErrorType

@dataclass
class Case:
    text: str
    expect_error: bool = True
    error_type: SpellErrorType | None = None

FILE_ERROR_MAPPING = {
    "spacing.tsv": SpellErrorType.SPACING_RAW,
    "spelling.tsv": SpellErrorType.SPELLING_RAW,
}

def load_cases_from_tsv(file_path: Path) -> list[Case]:
    cases = []
    
    if not file_path.exists():
        print(f"\n[Warning] {file_path.name} 파일이 없습니다. 해당 케이스를 건너뜁니다.")
        return cases

    error_type = FILE_ERROR_MAPPING.get(file_path.name)
    
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
TEST_DATA_DIR = CURRENT_DIR / "raw_data"
ALL_CASES = []

for filename in FILE_ERROR_MAPPING.keys():
    file_path = TEST_DATA_DIR / filename
    ALL_CASES.extend(load_cases_from_tsv(file_path))


class TestSpellChecker:
    @pytest.fixture(autouse=True)
    def setup(self, searcher):
        searcher.add_word_from_list(RAW_STRING_RULES)
        self.searcher = searcher

    @pytest.mark.parametrize(
        "c", 
        ALL_CASES, 
        ids=lambda c: f"{'ERROR' if c.expect_error else 'PASS'}-{c.text[:15]}"
    )
    def test_raw_string_searcher_from_tsv(self, c: Case):
        errors = list(self.searcher.search(c.text))

        if c.expect_error:
            assert_error_raw_text(errors, c.text)
            if c.error_type:
                check_error_type(errors, c.error_type)
        else:
            assert_no_errors_raw_text(errors, c.text)