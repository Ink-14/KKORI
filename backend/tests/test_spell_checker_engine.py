import time

import pytest

from src.models.interface import Tag, SpellError, SpellErrorType
from src.engines.spell_checker import SpellChecker
from src.engines.configs.rule import SPELL_CHECK_RULES
from src.engines.configs.rule_builder import *
from tests.helpers import build_tokens

# ── 헬퍼 ──

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


# ── BOS spacing ──

BOS_SPACING_RULES = [
    *rule()
    .form("A")
    .if_spaced()
    .form("B")
    .msg("spaced at bos")
    .build(),

    *rule()
    .form("A")
    .if_not_spaced()
    .form("B")
    .msg("attached at bos")
    .build(),
]

class TestBosSpacing:
    """첫 토큰(BOS)에서 SPACED/ATTACHED 규칙이 잘못 매칭되지 않는지 검증"""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.checker = SpellChecker()
        self.checker.add_rule_from_list(BOS_SPACING_RULES)

    def test_spaced_rule_does_not_match_at_bos(self):
        tokens = build_tokens(("A", Tag.일반명사), " ", ("B", Tag.일반명사))
        errors = list(self.checker.check(tokens))
        assert all(e.error_message != "spaced at bos" for e in errors)

    def test_attached_rule_does_not_match_at_bos(self):
        tokens = build_tokens(("A", Tag.일반명사), ("B", Tag.일반명사))
        errors = list(self.checker.check(tokens))
        assert all(e.error_message != "attached at bos" for e in errors)

    def test_spaced_rule_matches_mid_sentence(self):
        tokens = build_tokens(("X", Tag.일반명사), " ", ("A", Tag.일반명사), " ", ("B", Tag.일반명사))
        errors = list(self.checker.check(tokens))
        assert_found(errors, "spaced at bos", 2, 5)

    def test_attached_rule_matches_mid_sentence(self):
        tokens = build_tokens(("X", Tag.일반명사), ("A", Tag.일반명사), ("B", Tag.일반명사))
        errors = list(self.checker.check(tokens))
        assert_found(errors, "attached at bos", 1, 3)


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
    .NOT(form("N"))
    .context()
    .form("A")
    .form("B")
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
    .form("1")
    .form("2")
    .NOT(form("3"))
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
        tokens = build_tokens(("A", Tag.일반명사), ("B", Tag.일반명사), ("C", Tag.일반명사))
        errors = list(self.checker.check(tokens))
        assert_found(errors, "bos epsilon", 0, 2)

    def test_bos_false_case(self):
        tokens = build_tokens(("N", Tag.일반명사), ("A", Tag.일반명사), ("B", Tag.일반명사))
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
        tokens = build_tokens(("1", Tag.일반명사), ("2", Tag.일반명사))
        errors = list(self.checker.check(tokens))
        assert_found(errors, "eof epsilon", 0, 2)
        
    def test_eof_false_case(self):
        tokens = build_tokens(("1", Tag.일반명사), ("2", Tag.일반명사), ("3", Tag.일반명사))
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
    .AND(tag(Tag.숫자), longer(1))
    .msg("OR-AND 조건 검사")
    .build(),
    
    *rule()
    .AND(first(), batchim("ᆸ"), longer(1))
    .AND(NOT(tag(Tag.일반명사)), form("0"))
    .msg("AND-NOT 조건 검사")
    .build(),
    
    *rule()
    .AND(NOT(batchim("ᆯ")), any_batchim())
    .OR(form("0"), tag(Tag.대명사))
    .AND(longer(4), tag(Tag.일반명사))
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

# ── message 기준 dedup 테스트 ──

DEDUP_RULES = [
    *rule()
    .form("A").context()
    .form("B")
    .msg("출력").build(),

    *rule()
    .form("B")
    .form("A").context()
    .msg("출력").build(),

    *rule()
    .form("B")
    .NOT(form("A")).context()
    .msg("출력2").build(),
]

class TestMessageDedup:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.checker = SpellChecker()
        self.checker.add_rule_from_list(DEDUP_RULES)

    def test_dedup_message(self):
        tokens = build_tokens(("A", Tag.일반명사), ("B", Tag.일반명사), ("A", Tag.일반명사))
        errors = list(self.checker.check(tokens))
        # message dedup으로 1개만 발생
        assert len(errors) == 1

    def test_not_dedup_by_diff_message(self):
        tokens = build_tokens(("A", Tag.일반명사), ("B", Tag.일반명사), ("C", Tag.일반명사))
        errors = list(self.checker.check(tokens))
        # message 다른 경우에는 출력
        assert any(e.error_message == "출력" for e in errors)
        assert any(e.error_message == "출력2" for e in errors)

# ── 겹침 억제 (priority / SUPPRESS_ALL) ──
# 규칙: 쌍(pairwise)으로 구간이 조금이라도 교차하는 매치끼리만 비교.
#   - SUPPRESS_ALL: 자신은 출력되지 않고, 겹치는 상대를 무조건 억제.
#   - priority가 더 높은(숫자가 작은) 쪽이 이기고, 겹치는 상대를 억제.
#   - priority가 동률이면 서로 억제하지 않음 (둘 다 출력).
#   - 애초에 구간이 겹치지 않으면 비교 자체를 하지 않음 (둘 다 출력).

def rule_type(error_type: SpellErrorType) -> RuleBuilder:
    return RuleBuilder(error_type)

SUPPRESS_ALL_ONLY = [
    *rule_type(SpellErrorType.SUPPRESS_ALL)
    .form("S")
    .msg("suppress_all 자체 출력")
    .build(),
]

SUPPRESS_ALL_VS_NORMAL = [
    *rule_type(SpellErrorType.SUPPRESS_ALL)
    .form("A")
    .form("B")
    .msg("억제자")
    .build(),

    *rule_type(SpellErrorType.SPELLING)
    .form("B")
    .form("C")
    .msg("억제당함")
    .build(),
]

SUPPRESS_ALL_NON_OVERLAPPING = [
    *rule_type(SpellErrorType.SUPPRESS_ALL)
    .form("A")
    .form("B")
    .msg("억제자")
    .build(),

    *rule_type(SpellErrorType.SPELLING)
    .form("X")
    .form("Y")
    .msg("무관한 규칙")
    .build(),
]

COMPLEX_VS_SPELLING = [
    *rule_type(SpellErrorType.COMPLEX)
    .form("A")
    .form("B")
    .msg("COMPLEX 승리")
    .build(),

    *rule_type(SpellErrorType.SPELLING)
    .form("B")
    .form("C")
    .msg("SPELLING 패배")
    .build(),
]

SAME_PRIORITY_OVERLAP = [
    *rule_type(SpellErrorType.SPELLING)
    .form("A")
    .form("B")
    .msg("SPELLING 동시출력")
    .build(),

    *rule_type(SpellErrorType.SPACING)
    .form("B")
    .form("C")
    .msg("SPACING 동시출력")
    .build(),
]

# 기본 priority는 둘 다 2(동률)라 겹쳐도 함께 살아남지만,
# 한쪽에 .rank()로 더 높은 우선순위(작은 숫자)를 줘서 결과를 뒤집는다.
RANK_OVERRIDE_FLIPS_RESULT = [
    *rule_type(SpellErrorType.SPELLING)
    .form("A")
    .form("B")
    .rank(0)
    .msg("rank로 승격된 SPELLING")
    .build(),

    *rule_type(SpellErrorType.SPACING)
    .form("B")
    .form("C")
    .msg("기본 우선순위 SPACING")
    .build(),
]

ADJACENT_NOT_OVERLAPPING = [
    *rule_type(SpellErrorType.COMPLEX)
    .form("A")
    .form("B")
    .msg("COMPLEX 인접")
    .build(),

    *rule_type(SpellErrorType.SPELLING)
    .form("C")
    .form("D")
    .msg("SPELLING 인접")
    .build(),
]

CONTAINED_OVERLAP = [
    *rule_type(SpellErrorType.SPELLING)
    .form("A")
    .form("B")
    .form("C")
    .form("D")
    .msg("SPELLING 전체포함")
    .build(),

    *rule_type(SpellErrorType.COMPLEX)
    .form("B")
    .form("C")
    .msg("COMPLEX 내부포함")
    .build(),
]

CHAIN_PAIRWISE_RULES = [
    *rule_type(SpellErrorType.SPELLING)
    .form("A")
    .form("B")
    .msg("A_체인")
    .build(),

    *rule_type(SpellErrorType.COMPLEX)
    .form("B")
    .form("C")
    .msg("B_체인")
    .build(),

    *rule_type(SpellErrorType.SPELLING)
    .form("C")
    .form("D")
    .msg("C_체인")
    .build(),
]

class TestOverlapSuppression:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.checker = SpellChecker()

    def test_suppress_all_never_emitted_alone(self):
        self.checker.add_rule_from_list(SUPPRESS_ALL_ONLY)
        tokens = build_tokens(("S", Tag.일반명사))
        errors = list(self.checker.check(tokens))
        assert_empty(errors)

    def test_suppress_all_suppresses_overlapping_rule(self):
        self.checker.add_rule_from_list(SUPPRESS_ALL_VS_NORMAL)
        # A(0,1) B(1,2) -> 억제자 span(0,2), C(2,3) -> 억제당함 span(1,3), 서로 교차
        tokens = build_tokens(("A", Tag.일반명사), ("B", Tag.일반명사), ("C", Tag.일반명사))
        errors = list(self.checker.check(tokens))
        assert_empty(errors)

    def test_suppress_all_does_not_affect_non_overlapping_rule(self):
        self.checker.add_rule_from_list(SUPPRESS_ALL_NON_OVERLAPPING)
        tokens = build_tokens(
            ("A", Tag.일반명사), ("B", Tag.일반명사),
            ("X", Tag.일반명사), ("Y", Tag.일반명사),
        )
        errors = list(self.checker.check(tokens))
        assert_found(errors, "무관한 규칙", 2, 4)
        assert all(e.error_message != "억제자" for e in errors)

    def test_higher_priority_suppresses_lower(self):
        self.checker.add_rule_from_list(COMPLEX_VS_SPELLING)
        tokens = build_tokens(("A", Tag.일반명사), ("B", Tag.일반명사), ("C", Tag.일반명사))
        errors = list(self.checker.check(tokens))
        assert_found(errors, "COMPLEX 승리", 0, 2)
        assert all(e.error_message != "SPELLING 패배" for e in errors)

    def test_same_priority_both_survive(self):
        self.checker.add_rule_from_list(SAME_PRIORITY_OVERLAP)
        tokens = build_tokens(("A", Tag.일반명사), ("B", Tag.일반명사), ("C", Tag.일반명사))
        errors = list(self.checker.check(tokens))
        assert_found(errors, "SPELLING 동시출력", 0, 2)
        assert_found(errors, "SPACING 동시출력", 1, 3)

    def test_rank_override_flips_suppression_result(self):
        # 둘 다 기본 priority(2)였다면 동률로 공존했겠지만, SPELLING 쪽에
        # rank(0)을 줘서 겹치는 SPACING을 억제하도록 뒤집는다.
        self.checker.add_rule_from_list(RANK_OVERRIDE_FLIPS_RESULT)
        tokens = build_tokens(("A", Tag.일반명사), ("B", Tag.일반명사), ("C", Tag.일반명사))
        errors = list(self.checker.check(tokens))
        assert_found(errors, "rank로 승격된 SPELLING", 0, 2)
        assert all(e.error_message != "기본 우선순위 SPACING" for e in errors)

    def test_adjacent_non_overlapping_both_survive(self):
        # A(0,1) B(1,2) -> span(0,2), C(2,3) D(3,4) -> span(2,4). 경계가 맞닿을 뿐 교차하지 않음.
        self.checker.add_rule_from_list(ADJACENT_NOT_OVERLAPPING)
        tokens = build_tokens(
            ("A", Tag.일반명사), ("B", Tag.일반명사),
            ("C", Tag.일반명사), ("D", Tag.일반명사),
        )
        errors = list(self.checker.check(tokens))
        assert_found(errors, "COMPLEX 인접", 0, 2)
        assert_found(errors, "SPELLING 인접", 2, 4)

    def test_fully_contained_overlap_is_compared(self):
        # SPELLING span(0,4)이 COMPLEX span(1,3)을 완전히 포함 -> 교차로 간주, priority 낮은 SPELLING 억제
        self.checker.add_rule_from_list(CONTAINED_OVERLAP)
        tokens = build_tokens(
            ("A", Tag.일반명사), ("B", Tag.일반명사),
            ("C", Tag.일반명사), ("D", Tag.일반명사),
        )
        errors = list(self.checker.check(tokens))
        assert_found(errors, "COMPLEX 내부포함", 1, 3)
        assert all(e.error_message != "SPELLING 전체포함" for e in errors)

    def test_pairwise_chain_not_transitive(self):
        # A_체인(0,2)-B_체인(1,3) 교차 -> B(COMPLEX)가 이겨서 A 억제
        # B_체인(1,3)-C_체인(2,4) 교차 -> B(COMPLEX)가 이겨서 C 억제
        # A_체인과 C_체인은 서로 교차하지 않으므로 직접 비교되지 않음 (결과에 영향 없음, 어차피 둘 다 B에 의해 죽음)
        self.checker.add_rule_from_list(CHAIN_PAIRWISE_RULES)
        tokens = build_tokens(
            ("A", Tag.일반명사), ("B", Tag.일반명사),
            ("C", Tag.일반명사), ("D", Tag.일반명사),
        )
        errors = list(self.checker.check(tokens))
        assert_found(errors, "B_체인", 1, 3)
        assert all(e.error_message != "A_체인" for e in errors)
        assert all(e.error_message != "C_체인" for e in errors)

    def test_check_batch_applies_same_suppression(self):
        self.checker.add_rule_from_list(SUPPRESS_ALL_VS_NORMAL)
        tokens = build_tokens(("A", Tag.일반명사), ("B", Tag.일반명사), ("C", Tag.일반명사))
        batch_errors = self.checker.check_batch([tokens])
        assert_empty(batch_errors[0])

    def test_check_batch_keeps_same_priority_pair(self):
        self.checker.add_rule_from_list(SAME_PRIORITY_OVERLAP)
        tokens = build_tokens(("A", Tag.일반명사), ("B", Tag.일반명사), ("C", Tag.일반명사))
        batch_errors = self.checker.check_batch([tokens])
        errors = batch_errors[0]
        assert_found(errors, "SPELLING 동시출력", 0, 2)
        assert_found(errors, "SPACING 동시출력", 1, 3)


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
        self.checker = SpellChecker(debug=True)
        self.checker.add_rule_from_list(SPELL_CHECK_RULES)

    def test_massive_token_stream_performance_with_default_config(self):
        TOKEN_COUNT = 10000
        tokens = build_tokens(*[("테스트", Tag.일반명사) for _ in range(TOKEN_COUNT)])
        
        start_time = time.perf_counter()
        
        errors = list(self.checker.check(tokens))
        
        end_time = time.perf_counter()
        elapsed = end_time - start_time

        total_rule_id = {i.rule_id for i in self.checker._registry}

        print(f"{self.checker.stats()}")
        print(f"규칙 id 개수: {len(total_rule_id)}")
        print(f"빌드 후의 규칙 개수: {len(self.checker._registry)}개")
        print(f"규칙당 평균 조건 개수: {self.checker.total_steps / len(self.checker._registry)}개")
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