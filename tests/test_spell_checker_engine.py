import time
from dataclasses import dataclass

import pytest

from korean_spell_checker.models.interface import Tag, SpellError, SpellErrorType
from korean_spell_checker.engines.spell_checker import SpellChecker
from korean_spell_checker.configs.spell_checker_config import SPELL_CHECK_RULES
from korean_spell_checker.configs.spell_checker_config_builder import *
from korean_spell_checker.utils.hangul import get_jongseong, is_jamo

# ── 헬퍼 ──

@dataclass
class DummyToken:
    form: str
    tag: str
    start: int
    end: int
    lemma: str = ""

    @property
    def len(self) -> int:
        return self.end - self.start

    @property
    def batchim(self) -> str:
        last = self.form[-1]
        return last if is_jamo(last) else get_jongseong(last)

def build_tokens(*args) -> list[DummyToken]:
    tokens = []
    pos = 0
    for arg in args:
        if arg == " ":
            pos += 1
            continue
        form, tag = arg
        tokens.append(DummyToken(form=form, tag=tag, start=pos, end=pos + len(form)))
        pos += len(form)
    return tokens

def assert_found(errors: list[SpellError], msg: str, start: int, end: int):
    assert any(
        e.error_message == msg and e.start_index == start and e.end_index == end
        for e in errors
    ), f"Expected ({msg!r}, {start}, {end}) not found in {errors}"

def assert_empty(errors: list):
    assert len(errors) == 0, f"Expected no errors, got {errors}"

def rule() -> RuleBuilder:
    return RuleBuilder(SpellErrorType.TEST)

# ── 띄어쓰기 판정 ──

SPACING_RULES = [
    *rule()
    .form("A")
    .form("B")
    .if_spaced()
    .msg("spaced 오류")
    .build(),

    *rule()
    .form("A")
    .form("B")
    .if_not_spaced()
    .msg("attached 오류")
    .build(),
]

class TestSpacing:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.checker = SpellChecker()
        self.checker.add_rule_from_list(SPACING_RULES)

    def test_spaced_triggers_spaced_rule(self):
        tokens = build_tokens(("A", Tag.일반명사), " ", ("B", Tag.일반명사))
        errors = list(self.checker.check(tokens))
        assert_found(errors, "spaced 오류", 0, 3)

    def test_spaced_does_not_trigger_attached_rule(self):
        tokens = build_tokens(("A", Tag.일반명사), " ", ("B", Tag.일반명사))
        errors = list(self.checker.check(tokens))
        assert all(e.error_message != "attached 오류" for e in errors)

    def test_attached_triggers_attached_rule(self):
        tokens = build_tokens(("A", Tag.일반명사), ("B", Tag.일반명사))
        errors = list(self.checker.check(tokens))
        assert_found(errors, "attached 오류", 0, 2)

    def test_attached_does_not_trigger_spaced_rule(self):
        tokens = build_tokens(("A", Tag.일반명사), ("B", Tag.일반명사))
        errors = list(self.checker.check(tokens))
        assert all(e.error_message != "spaced 오류" for e in errors)


# ── 옵셔널 전이 ──

OPTIONAL_RULES = [
    *rule()
    .form("A")
    .form("B")
    .opt()
    .form("C")
    .msg("optional 매칭")
    .build(),
]

class TestOptional:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.checker = SpellChecker()
        self.checker.add_rule_from_list(OPTIONAL_RULES)

    def test_with_optional_present(self):
        tokens = build_tokens(("A", Tag.일반명사), ("B", Tag.일반명사), ("C", Tag.일반명사))
        errors = list(self.checker.check(tokens))
        assert_found(errors, "optional 매칭", 0, 3)

    def test_with_optional_skipped(self):
        tokens = build_tokens(("A", Tag.일반명사), ("C", Tag.일반명사))
        errors = list(self.checker.check(tokens))
        assert_found(errors, "optional 매칭", 0, 2)

    def test_no_match_without_required(self):
        tokens = build_tokens(("A", Tag.일반명사), ("D", Tag.일반명사))
        errors = list(self.checker.check(tokens))
        assert_empty(errors)

BOS_EPSILON = [
    *rule()
    .NOT(form("BOS_NOT"))
    .context()
    .form("BOS_A")
    .form("BOS_B")
    .msg("bos epsilon")
    .build(),

    *rule()
    .NOT(form("a"))
    .form("b")
    .form("c")
    .msg("bos epsilon false case")
    .build(),
]

EOF_EPSILON = [
    *rule()
    .form("EOF_A")
    .form("EOF_B")
    .NOT(form("EOF_NOT"))
    .context()
    .msg("eof epsilon")
    .build(),
]

class TestEpsilonTransition:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.checker = SpellChecker()
        self.checker.add_rule_from_list(BOS_EPSILON)
        self.checker.add_rule_from_list(EOF_EPSILON)

    def test_bos_epsilon(self):
        tokens = build_tokens(("BOS_A", Tag.일반명사), ("BOS_B", Tag.일반명사), ("BOS_C", Tag.일반명사))
        errors = list(self.checker.check(tokens))
        assert_found(errors, "bos epsilon", 0, 10)

    def test_bos_false_case(self):
        tokens = build_tokens(("BOS_NOT", Tag.일반명사), ("BOS_A", Tag.일반명사), ("BOS_B", Tag.일반명사))
        errors = list(self.checker.check(tokens))
        assert_empty(errors)

    def test_bos_should_transit(self):
        tokens = build_tokens(("d", Tag.일반명사), ("b", Tag.일반명사), ("c", Tag.일반명사))
        errors = list(self.checker.check(tokens))
        assert_found(errors, "bos epsilon false case", 0, 3)

    def test_bos_should_not_transit(self):
        tokens = build_tokens(("a", Tag.일반명사), ("b", Tag.일반명사), ("c", Tag.일반명사))
        errors = list(self.checker.check(tokens))
        assert_empty(errors)

    def test_eof_epsilon(self):
        tokens = build_tokens(("EOF_A", Tag.일반명사), ("EOF_B", Tag.일반명사))
        errors = list(self.checker.check(tokens))
        assert_found(errors, "eof epsilon", 0, 10)
        
    def test_eof_false_case(self):
        tokens = build_tokens(("EOF_A", Tag.일반명사), ("EOF_B", Tag.일반명사), ("EOF_NOT", Tag.일반명사))
        errors = list(self.checker.check(tokens))
        assert_empty(errors)    
        
# ── shortest match ──

SHORTEST_MATCH_RULES = [
    *rule()
    .form("A")
    .form("A")
    .opt()
    .form("B")
    .msg("shortest")
    .build(),
]

class TestShortestMatch:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.checker = SpellChecker()
        self.checker.add_rule_from_list(SHORTEST_MATCH_RULES)

    def test_shortest_match_preferred(self):
        # 커서1: A(0)→A(1)→B(2) = span (0,3)
        # 커서2: A(1)→[opt skip]→B(2) = span (1,3)
        # 같은 스텝에서 둘 다 output 도달 → 짧은 (1,3) 선택
        tokens = build_tokens(
            ("A", Tag.일반명사), ("A", Tag.일반명사),
            ("B", Tag.일반명사), ("B", Tag.일반명사),
        )
        errors = list(self.checker.check(tokens))
        matches = [e for e in errors if e.error_message == "shortest"]
        assert any(e.end_index - e.start_index == 2 for e in matches)  # span 2짜리가 존재
        assert all(e.end_index - e.start_index != 3 for e in matches)   # 긴 매치는 없어야 함


# ── 엣지 케이스 ──

class TestEdgeCases:
    def test_empty_tokens(self):
        checker = SpellChecker()
        checker.add_rule_from_list(SPACING_RULES)
        errors = list(checker.check([]))
        assert_empty(errors)

    def test_no_rules_raises(self):
        checker = SpellChecker()
        with pytest.raises(ValueError):
            list(checker.check([]))

    def test_add_rule_after_check_raises(self):
        checker = SpellChecker()
        checker.add_rule_from_list(SPACING_RULES)
        list(checker.check([]))
        with pytest.raises(RuntimeError):
            checker.add_rule_from_list(SPACING_RULES)

    def test_single_token_no_crash(self):
        checker = SpellChecker()
        checker.add_rule_from_list(SPACING_RULES)
        tokens = build_tokens(("A", Tag.일반명사))
        errors = list(checker.check(tokens))
        assert_empty(errors)


# ── 연속 조건 ──

SAME_STRING_1 = [
    *rule()
    .form("A")
    .form("B")
    .msg("연속 매치")
    .build(),
]

SAME_STRING_2 = [
    *rule()
    .tag(Tag.숫자)
    .tag(Tag.숫자)
    .msg("연속 매치")
    .build(),
]

class TestSameStringMatch:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.checker = SpellChecker()
        
    def test_multiple_matches_in_same_string_1(self):
        self.checker.add_rule_from_list(SAME_STRING_1)
        tokens = build_tokens(("A", Tag.일반명사), ("B", Tag.일반명사), ("A", Tag.일반명사), ("B", Tag.일반명사))
        errors = list(self.checker.check(tokens))
        assert len(errors) == 2
        
    def test_multiple_matches_in_same_string_2(self):
        """결과: (0, 1), (1, 2), (2, 3) == 3개 필요
        """
        self.checker.add_rule_from_list(SAME_STRING_2)
        tokens = build_tokens(("1", Tag.숫자), ("2", Tag.숫자), ("3", Tag.숫자), ("4", Tag.숫자))
        errors = list(self.checker.check(tokens))
        assert len(errors) == 3

# ── context ──

CONTEXT_MATCH = [
    *rule()
    .form("A")
    .context()
    .form("B")
    .form("C")
    .msg("context 매치")
    .build(),
    
    *rule()
    .form("1")
    .form("2")
    .form("3")
    .context()
    .msg("context 매치")
    .build(),
    
    *rule()
    .form("a")
    .form("b")
    .context()
    .form("c")
    .msg("context 매치")
    .build(),
]

class TestContextMatch:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.checker = SpellChecker()
        
    def test_context_match_prefix(self):
        self.checker.add_rule_from_list(CONTEXT_MATCH)
        tokens = build_tokens(("A", Tag.일반명사), ("B", Tag.일반명사), ("C", Tag.일반명사))
        errors = list(self.checker.check(tokens))
        assert_found(errors, "context 매치", 1, 3)
        
    def test_context_match_suffix(self):
        self.checker.add_rule_from_list(CONTEXT_MATCH)
        tokens = build_tokens(("1", Tag.일반명사), ("2", Tag.일반명사), ("3", Tag.일반명사))
        errors = list(self.checker.check(tokens))
        assert_found(errors, "context 매치", 0, 2)
        
    def test_context_match_in_middle(self):
        self.checker.add_rule_from_list(CONTEXT_MATCH)
        tokens = build_tokens(("a", Tag.일반명사), ("b", Tag.일반명사), ("c", Tag.일반명사))
        errors = list(self.checker.check(tokens))
        assert_found(errors, "context 매치", 0, 3)


# ── 복합 조건 ──

COMPLEX_CONDITION = [
    *rule()
    .AND(tag(Tag.일반명사), form("밥"))
    .AND(tag(Tag.숫자), form("0"))
    .msg("AND 조건 검사")
    .build(),
    
    *rule()
    .OR(tag(Tag.일반명사), tag(Tag.숫자))
    .AND(tag(Tag.숫자), length(1))
    .msg("OR-AND 조건 검사")
    .build(),
    
    *rule()
    .AND(first(), batchim("ᆸ"), length(1))
    .AND(NOT(tag(Tag.일반명사)), form("0"))
    .msg("AND-NOT 조건 검사")
    .build(),
    
    *rule()
    .AND(NOT(batchim("ᆯ")), any_batchim())
    .OR(form("0"), tag(Tag.대명사))
    .AND(length(4), tag(Tag.일반명사))
    .msg("첫 토큰 NOT 조건 검사")
    .build(),
    
    *rule()
    .form("a")
    .context()
    .form("b")
    .context()
    .opt()
    .form("c")
    .msg("context-opt 조합 검사")
    .build(),
]

class TestComplexCondition:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.checker = SpellChecker()
        self.checker.add_rule_from_list(COMPLEX_CONDITION)
        
    def test_complex_condition(self):
        tokens = build_tokens(("밥", Tag.일반명사), ("0", Tag.숫자), ("아미타불", Tag.일반명사))
        errors = list(self.checker.check(tokens))
        assert_found(errors, "AND 조건 검사", 0, 2)
        assert_found(errors, "OR-AND 조건 검사", 0, 2)
        assert_found(errors, "AND-NOT 조건 검사", 0, 2)
        assert_found(errors, "첫 토큰 NOT 조건 검사", 0, 6)
        
    def test_complex_condition_not_found(self):
        tokens = build_tokens(("밤", Tag.일반명사), ("1", Tag.숫자))
        errors = list(self.checker.check(tokens))
        assert_found(errors, "OR-AND 조건 검사", 0, 2)
        assert all(e.error_message != "AND 조건 검사" for e in errors), "AND 조건 검사가 발생하지 않아야 합니다."
        assert all(e.error_message != "AND-NOT 조건 검사" for e in errors), "AND-NOT 조건 검사가 발생하지 않아야 합니다."
        
    def test_complex_condition_context_and_opt(self):
        tokens = build_tokens(("a", Tag.일반명사), ("b", Tag.숫자), ("c", Tag.일반명사))
        errors = list(self.checker.check(tokens))
        assert_found(errors, "context-opt 조합 검사", 2, 3)
        
# ── opt 중복 출력 방지 ──
# 재현 조건: opt 전이의 epsilon skip 경로와 normal 경로가 동시에 유효할 때
# (opt 토큰이 뒤따르는 NOT 조건도 만족하는 경우) 출력 노드가 다른 타임스텝에서
# 두 번 활성화되어 같은 에러가 중복 출력되던 버그 수정 검증.

OPT_DUPLICATE_RULES = [
    *rule()
    .form("A")
    .form("OPT")
    .opt()
    .NOT(form("BLOCK"))
    .msg("opt 중복 방지")
    .build(),
]

class TestOptionalNoDuplicate:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.checker = SpellChecker()
        self.checker.add_rule_from_list(OPT_DUPLICATE_RULES)

    def test_opt_present_fires_once(self):
        # OPT가 NOT(BLOCK)도 만족 → epsilon skip 경로와 normal 경로 모두 출력 노드에 도달
        # 수정 전: 에러 2개, 수정 후: 에러 1개
        tokens = build_tokens(("A", Tag.일반명사), ("OPT", Tag.일반명사), ("X", Tag.일반명사))
        errors = [e for e in self.checker.check(tokens) if e.error_message == "opt 중복 방지"]
        assert len(errors) == 1

    def test_opt_absent_fires_once(self):
        tokens = build_tokens(("A", Tag.일반명사), ("X", Tag.일반명사))
        errors = [e for e in self.checker.check(tokens) if e.error_message == "opt 중복 방지"]
        assert len(errors) == 1

    def test_block_directly_after_a_suppresses(self):
        # A 바로 뒤에 BLOCK → NOT(BLOCK) 실패, epsilon skip도 BLOCK을 만나므로 매칭 없음
        tokens = build_tokens(("A", Tag.일반명사), ("BLOCK", Tag.일반명사))
        errors = [e for e in self.checker.check(tokens) if e.error_message == "opt 중복 방지"]
        assert len(errors) == 0

    def test_multiple_positions_each_fire_once(self):
        # 두 위치에서 매칭 → 각 1번씩 총 2번
        tokens = build_tokens(
            ("A", Tag.일반명사), ("OPT", Tag.일반명사), ("X", Tag.일반명사),
            ("A", Tag.일반명사), ("OPT", Tag.일반명사), ("X", Tag.일반명사),
        )
        errors = [e for e in self.checker.check(tokens) if e.error_message == "opt 중복 방지"]
        assert len(errors) == 2


# prefix를 공유하는 두 규칙에서 중간 노드가 출력 노드이면서 outgoing transition도 있는 케이스.
# yielded_outputs 체크가 커서 흐름이 아닌 출력에만 작용하므로 두 번째 출력이 억제되지 않아야 함.

CHAIN_OUTPUT_RULES = [
    *rule()
    .form("P")
    .form("Q")
    .msg("PQ 출력")
    .build(),

    *rule()
    .form("P")
    .form("Q")
    .form("R")
    .msg("PQR 출력")
    .build(),
]

class TestChainOutputNotSuppressed:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.checker = SpellChecker()
        self.checker.add_rule_from_list(CHAIN_OUTPUT_RULES)

    def test_both_outputs_fire(self):
        # N_PQ는 출력 노드이면서 N_PQR로 가는 전이도 보유 → 두 출력 모두 발생해야 함
        tokens = build_tokens(("P", Tag.일반명사), ("Q", Tag.일반명사), ("R", Tag.일반명사))
        errors = list(self.checker.check(tokens))
        assert any(e.error_message == "PQ 출력" for e in errors)
        assert any(e.error_message == "PQR 출력" for e in errors)

    def test_shorter_rule_only(self):
        tokens = build_tokens(("P", Tag.일반명사), ("Q", Tag.일반명사))
        errors = list(self.checker.check(tokens))
        assert any(e.error_message == "PQ 출력" for e in errors)
        assert all(e.error_message != "PQR 출력" for e in errors)


# ── 스트레스 & 성능 벤치마크 테스트 ──

STRESS_RULES = [
    *rule()
    .tag(Tag.일반명사)
    .tag(Tag.일반명사)
    .opt()
    .tag(Tag.일반명사)
    .opt()
    .msg("스트레스 매칭")
    .build(),
]

@pytest.mark.perf
class TestEnginePerformance:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.checker = SpellChecker()
        self.checker.add_rule_from_list(STRESS_RULES)

    def test_linear_scaling(self):
        """시간 복잡도가 선형인지 검증"""
        
        tokens_5k = build_tokens(*[("테스트", Tag.일반명사) for _ in range(5000)])
        tokens_10k = build_tokens(*[("테스트", Tag.일반명사) for _ in range(10000)])

        start = time.perf_counter()
        list(self.checker.check(tokens_5k))
        time_5k = time.perf_counter() - start

        start = time.perf_counter()
        list(self.checker.check(tokens_10k))
        time_10k = time.perf_counter() - start

        ratio = time_10k / time_5k
        print(f"\n[스케일링] 5K: {time_5k:.4f}초, 10K: {time_10k:.4f}초, 비율: {ratio:.2f}x")

        # 선형이면 ~2.0x, O(n²)이면 ~4.0x
        # 여유를 두고 3.0x 이하면 통과
        assert ratio < 3.0, f"비선형 스케일링 감지! 비율: {ratio:.2f}x"

@pytest.mark.perf
class TestEnginePerformanceWithDefaultConfig:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.checker = SpellChecker()
        self.checker.add_rule_from_list(SPELL_CHECK_RULES)

    def test_massive_token_stream_performance_with_default_config(self):
        TOKEN_COUNT = 10000
        tokens = build_tokens(*[("테스트", Tag.일반명사) for _ in range(TOKEN_COUNT)])
        
        start_time = time.perf_counter()
        
        errors = list(self.checker.check(tokens))
        
        end_time = time.perf_counter()
        elapsed = end_time - start_time
        
        print(f"{self.checker.stats()}")
        print(f"[내장 규칙 성능 벤치마크] 토큰 {TOKEN_COUNT}개 처리 소요 시간: {elapsed:.4f}초")
        print(f"[내장 규칙 성능 벤치마크] 검출된 에러 개수: {len(errors)}개")
        
        assert elapsed < 1.0, f"엔진이 너무 느립니다! 상태 압축 실패. 소요 시간: {elapsed:.4f}초"

if __name__ == "__main__":
    import cProfile
    import pstats
    import io

    checker = SpellChecker()
    checker.add_rule_from_list(SPELL_CHECK_RULES)
    tokens = build_tokens(*[("테스트", Tag.일반명사) for _ in range(10000)])

    pr = cProfile.Profile()
    pr.enable()

    list(checker.check(tokens))

    pr.disable()

    s = io.StringIO()
    ps = pstats.Stats(pr, stream=s).sort_stats("cumulative")
    ps.print_stats(20)
    print(s.getvalue())