import pytest

@pytest.fixture(scope="session")
def tokenizer():
    from src.tokenizations.ko_tokenizer import KoTokenizer
    return KoTokenizer()

@pytest.fixture
def checker():
    from src.engines.spell_checker import SpellChecker
    return SpellChecker(debug=True)

@pytest.fixture
def searcher():
    from src.engines.raw_searcher import RawStringSearcher
    return RawStringSearcher()

@pytest.fixture(scope="session")
def configured_checker():
    """TSV 회귀 테스트용 (session scope, 규칙 1회만 빌드)"""
    from src.engines.spell_checker import SpellChecker
    from src.engines.configs.spell_checker_config import SPELL_CHECK_RULES
    c = SpellChecker()
    c.add_rule_from_list(SPELL_CHECK_RULES)
    return c