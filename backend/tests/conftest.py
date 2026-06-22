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
    from src.engines.configs.rule import SPELL_CHECK_RULES
    c = SpellChecker()
    c.add_rule_from_list(SPELL_CHECK_RULES)
    return c

def pytest_sessionfinish(session, exitstatus):
    from tests.test_spell_checker_default_config import ALL_CASES

    total = len(ALL_CASES)
    pending = sum(1 for c in ALL_CASES if c.is_pending)
    achieved = total - pending

    print("\n" + "=" * 50)
    print(f"스펙 커버리지: {achieved}/{total} ({achieved / total:.1%})")
    print(f"  - 통과 목표: {achieved}")
    print(f"  - pending: {pending}")
    print("=" * 50)