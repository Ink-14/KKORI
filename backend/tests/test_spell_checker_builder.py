import pytest

from src.models.interface import Tag, SpellErrorType
from src.models.spell_checker_classes import (
    TagCondition,
    FormCondition,
    LemmaCondition,
    BatchimCondition,
    AnyBatchimCondition,
    AnyCondition,
    TagAndFormCondition,
    FirstTokenCondition,
    LengthCondition,
    NotCondition,
    AndCondition,
    OrCondition,
    TagSetCondition,
    FormSetCondition,
    SpacingRule,
)
from src.engines.configs.spell_checker_config_builder import (
    RuleBuilder,
    CompiledMessage,
    tag,
    tags,
    form,
    forms,
    tag_form,
    lemma,
    longer,
    batchim,
    any_batchim,
    no_batchim,
    first,
    NOT,
    OR,
    AND,
)
from tests.helpers import build_tokens


# ── 헬퍼 ──

def rule() -> RuleBuilder:
    return RuleBuilder(SpellErrorType.TEST)


def first_cond(rules):
    """첫 번째 규칙의 첫 번째 step의 condition 반환."""
    return rules[0][0][0][0]


def first_step(rules):
    """첫 번째 규칙의 첫 번째 step (cond, spacing, opt, ctx) 반환."""
    return rules[0][0][0]


# ── 기본 조건 빌더 ──

class TestBasicConditions:
    def test_tag(self):
        rules = rule().tag(Tag.일반명사).msg("x").build()
        cond = first_cond(rules)
        assert isinstance(cond, TagCondition)
        assert cond.tag == Tag.일반명사

    def test_form(self):
        rules = rule().form("밥").msg("x").build()
        cond = first_cond(rules)
        assert isinstance(cond, FormCondition)
        assert cond.form == "밥"

    def test_lemma(self):
        rules = rule().lemma("먹다").msg("x").build()
        cond = first_cond(rules)
        assert isinstance(cond, LemmaCondition)
        assert cond.lemma == "먹다"

    def test_batchim(self):
        rules = rule().batchim("ᆯ").msg("x").build()
        cond = first_cond(rules)
        assert isinstance(cond, BatchimCondition)
        assert cond.batchim == "ᆯ"

    def test_any_batchim(self):
        rules = rule().any_batchim().msg("x").build()
        assert isinstance(first_cond(rules), AnyBatchimCondition)

    def test_no_batchim(self):
        rules = rule().no_batchim().msg("x").build()
        cond = first_cond(rules)
        assert isinstance(cond, BatchimCondition)
        assert cond.batchim == ""

    def test_any(self):
        rules = rule().any().msg("x").build()
        assert isinstance(first_cond(rules), AnyCondition)

    def test_tag_form(self):
        rules = rule().tag_form(Tag.일반명사, "밥").msg("x").build()
        cond = first_cond(rules)
        assert isinstance(cond, TagAndFormCondition)
        assert cond.tag == Tag.일반명사
        assert cond.form == "밥"

    def test_first(self):
        rules = rule().first().msg("x").build()
        assert isinstance(first_cond(rules), FirstTokenCondition)

    def test_longer(self):
        rules = rule().longer(3).msg("x").build()
        cond = first_cond(rules)
        assert isinstance(cond, LengthCondition)
        assert cond.length == 3


# ── set 조건 (다중 조건 전개) ──

class TestSetConditions:
    def test_tags_expands_to_multiple_rules(self):
        rules = rule().tags({Tag.일반명사, Tag.숫자}).msg("x").build()
        assert len(rules) == 2
        actual = {r[0][0][0].tag for r in rules}
        assert actual == {Tag.일반명사, Tag.숫자}

    def test_forms_expands_to_multiple_rules(self):
        rules = rule().forms({"밥", "국"}).msg("x").build()
        assert len(rules) == 2
        actual = {r[0][0][0].form for r in rules}
        assert actual == {"밥", "국"}

    def test_tags_single_element(self):
        rules = rule().tags({Tag.일반명사}).msg("x").build()
        assert len(rules) == 1
        cond = first_cond(rules)
        assert isinstance(cond, TagCondition)
        assert cond.tag == Tag.일반명사

    def test_cartesian_product_across_steps(self):
        # tags 2개 × forms 2개 = 4 규칙
        rules = (
            rule()
            .tags({Tag.일반명사, Tag.숫자})
            .forms({"A", "B"})
            .msg("x")
            .build()
        )
        assert len(rules) == 4


# ── 띄어쓰기 규칙 ──

class TestSpacing:
    def test_default_spacing_is_any(self):
        rules = rule().form("A").msg("x").build()
        _, spacing, _, _ = first_step(rules)
        assert spacing == SpacingRule.ANY

    def test_if_spaced_applies_to_last_step(self):
        rules = rule().form("A").form("B").if_spaced().msg("x").build()
        steps = rules[0][0]
        assert steps[0][1] == SpacingRule.ANY
        assert steps[1][1] == SpacingRule.SPACED

    def test_if_not_spaced_applies_to_last_step(self):
        rules = rule().form("A").if_not_spaced().form("B").msg("x").build()
        steps = rules[0][0]
        assert steps[0][1] == SpacingRule.ATTACHED
        assert steps[1][1] == SpacingRule.ANY

    def test_if_spaced_without_step_raises(self):
        with pytest.raises(ValueError):
            rule().if_spaced()

    def test_if_not_spaced_without_step_raises(self):
        with pytest.raises(ValueError):
            rule().if_not_spaced()


# ── optional ──

class TestOptional:
    def test_opt_sets_flag(self):
        rules = rule().form("A").form("B").opt().msg("x").build()
        steps = rules[0][0]
        assert steps[0][2] is False
        assert steps[1][2] is True

    def test_first_step_opt_raises(self):
        with pytest.raises(ValueError):
            rule().form("A").opt()

    def test_opt_without_step_raises(self):
        with pytest.raises(ValueError):
            rule().opt()


# ── context ──

class TestContext:
    def test_context_sets_flag(self):
        rules = rule().form("A").context().form("B").msg("x").build()
        steps = rules[0][0]
        assert steps[0][3] is True
        assert steps[1][3] is False

    def test_context_without_step_raises(self):
        with pytest.raises(ValueError):
            rule().context()

    def test_context_double_call_warns(self):
        with pytest.warns(UserWarning):
            rule().form("A").context().context()


# ── 검증 (validate) ──

class TestValidation:
    def test_no_steps_raises(self):
        with pytest.raises(ValueError):
            rule().msg("x").build()

    def test_no_message_raises(self):
        with pytest.raises(ValueError):
            rule().form("A").build()

    def test_not_set_error_type_raises(self):
        b = RuleBuilder(SpellErrorType.NOT_SET)
        with pytest.raises(ValueError):
            b.form("A").msg("x").build()

    def test_need_ml_judge_without_id_raises(self):
        b = RuleBuilder(SpellErrorType.NEED_ML_JUDGE)
        with pytest.raises(ValueError):
            b.form("A").msg("x").build()

    def test_need_ml_judge_with_id_passes(self):
        b = RuleBuilder(SpellErrorType.NEED_ML_JUDGE)
        rules = b.form("A").msg("x").id("R001").build()
        assert len(rules) == 1
        assert rules[0][3] == "R001"

    def test_all_steps_context_or_opt_raises(self):
        # 첫 step context, 두 번째 step opt → required step 없음
        with pytest.raises(ValueError):
            rule().form("A").context().form("B").opt().msg("x").build()

    def test_only_context_step_raises(self):
        with pytest.raises(ValueError):
            rule().form("A").context().msg("x").build()


# ── 빌더 메서드 체이닝 ──

class TestChaining:
    def test_methods_return_self(self):
        b = RuleBuilder(SpellErrorType.TEST)
        assert b.tag(Tag.일반명사) is b
        assert b.form("A") is b
        assert b.if_spaced() is b
        assert b.opt() is b
        assert b.msg("x") is b
        assert b.errtype(SpellErrorType.TEST) is b
        assert b.id("R1") is b

    def test_context_returns_self(self):
        b = RuleBuilder(SpellErrorType.TEST)
        b.form("A")
        assert b.context() is b

    def test_any_methods_return_self(self):
        b = RuleBuilder(SpellErrorType.TEST)
        assert b.any() is b
        assert b.any_batchim() is b
        assert b.no_batchim() is b
        assert b.first() is b


# ── AND/OR/NOT ──

class TestAndOrNot:
    def test_and_tag_form_optimizes_to_tag_and_form(self):
        rules = rule().AND(tag(Tag.일반명사), form("밥")).msg("x").build()
        cond = first_cond(rules)
        assert isinstance(cond, TagAndFormCondition)
        assert cond.tag == Tag.일반명사
        assert cond.form == "밥"

    def test_and_tag_form_with_other_wraps_in_and(self):
        rules = (
            rule()
            .AND(tag(Tag.일반명사), form("밥"), longer(2))
            .msg("x")
            .build()
        )
        cond = first_cond(rules)
        assert isinstance(cond, AndCondition)

    def test_and_multiple_tags_forms_cartesian(self):
        # tags(2) × forms(2) = 4개 TagAndFormCondition → 4개 규칙
        rules = (
            rule()
            .AND(tags({Tag.일반명사, Tag.숫자}), forms({"A", "B"}))
            .msg("x")
            .build()
        )
        assert len(rules) == 4
        for r in rules:
            assert isinstance(r[0][0][0], TagAndFormCondition)

    def test_and_only_other_conditions(self):
        rules = rule().AND(longer(2), any_batchim()).msg("x").build()
        cond = first_cond(rules)
        assert isinstance(cond, AndCondition)

    def test_or_expands_into_step_conditions(self):
        # OR(tag, tag) → 같은 step 내 2개 조건 → product에서 2개 규칙
        rules = rule().OR(tag(Tag.일반명사), tag(Tag.숫자)).msg("x").build()
        assert len(rules) == 2

    def test_not_form(self):
        rules = rule().NOT(form("X")).any().msg("x").build()
        cond = first_cond(rules)
        assert isinstance(cond, NotCondition)

    def test_not_single_tag_set(self):
        rules = rule().NOT(tags({Tag.일반명사})).any().msg("x").build()
        assert isinstance(first_cond(rules), NotCondition)

    def test_not_multi_tag_set(self):
        rules = rule().NOT(tags({Tag.일반명사, Tag.숫자})).any().msg("x").build()
        assert isinstance(first_cond(rules), NotCondition)

    def test_not_multi_form_set(self):
        rules = rule().NOT(forms({"A", "B"})).any().msg("x").build()
        assert isinstance(first_cond(rules), NotCondition)


# ── 모듈 레벨 헬퍼 함수 ──

class TestModuleHelpers:
    def test_tag(self):
        c = tag(Tag.일반명사)
        assert isinstance(c, TagCondition)
        assert c.tag == Tag.일반명사

    def test_form(self):
        c = form("밥")
        assert isinstance(c, FormCondition)
        assert c.form == "밥"

    def test_lemma(self):
        c = lemma("먹다")
        assert isinstance(c, LemmaCondition)
        assert c.lemma == "먹다"

    def test_longer(self):
        c = longer(5)
        assert isinstance(c, LengthCondition)
        assert c.length == 5

    def test_batchim(self):
        c = batchim("ᆯ")
        assert isinstance(c, BatchimCondition)
        assert c.batchim == "ᆯ"

    def test_any_batchim(self):
        assert isinstance(any_batchim(), AnyBatchimCondition)

    def test_no_batchim(self):
        c = no_batchim()
        assert isinstance(c, BatchimCondition)
        assert c.batchim == ""

    def test_first(self):
        assert isinstance(first(), FirstTokenCondition)

    def test_tag_form(self):
        c = tag_form(Tag.일반명사, "밥")
        assert isinstance(c, TagAndFormCondition)
        assert c.tag == Tag.일반명사
        assert c.form == "밥"

    def test_NOT_wraps(self):
        n = NOT(form("X"))
        assert isinstance(n, NotCondition)

    def test_OR_function(self):
        o = OR(tag(Tag.일반명사), tag(Tag.숫자))
        assert isinstance(o, OrCondition)

    def test_AND_function_tag_form_optimizes(self):
        c = AND(tag(Tag.일반명사), form("밥"))
        assert isinstance(c, TagAndFormCondition)
        assert c.tag == Tag.일반명사
        assert c.form == "밥"

    def test_AND_function_flattens_nested(self):
        inner = AND(longer(2), any_batchim())
        outer = AND(inner, form("밥"))
        assert isinstance(outer, AndCondition)


# ── 메시지 컴파일 ──

class TestMessage:
    def test_static_message_renders(self):
        rules = rule().form("A").msg("hello world").build()
        msg = rules[0][1]
        tokens = build_tokens(("A", Tag.일반명사))
        assert isinstance(msg, CompiledMessage)
        assert msg.render(tokens) == "hello world"

    def test_form_placeholder_renders(self):
        rules = rule().form("밥").msg("{form[0]}").build()
        msg = rules[0][1]
        tokens = build_tokens(("밥", Tag.일반명사))
        assert msg.render(tokens) == "밥"

    def test_form_index_out_of_range_raises(self):
        with pytest.raises(IndexError):
            rule().form("A").msg("{form[1]}").build()

    def test_form_placeholder_per_combo(self):
        # forms 다중 전개 시 각 규칙의 메시지가 자신의 form으로 렌더링
        rules = rule().forms({"밥", "국"}).msg("{form[0]}").build()
        tokens = build_tokens(("밥", Tag.일반명사))
        rendered = {r[1].render(tokens) for r in rules}
        assert rendered == {"밥", "국"}

    def test_dform_renders_from_tokens(self):
        rules = rule().tag(Tag.일반명사).msg("{dform[0]}").build()
        msg = rules[0][1]
        tokens = build_tokens(("밥", Tag.일반명사))
        assert msg.render(tokens) == "밥"

    def test_dform_multiple_indices(self):
        rules = (
            rule()
            .tag(Tag.일반명사)
            .tag(Tag.일반명사)
            .msg("{dform[0]}-{dform[1]}")
            .build()
        )
        msg = rules[0][1]
        tokens = build_tokens(("밥", Tag.일반명사), ("국", Tag.일반명사))
        assert msg.render(tokens) == "밥-국"

    def test_dtag_renders_from_tokens(self):
        rules = rule().tag(Tag.일반명사).msg("{dtag[0]}").build()
        msg = rules[0][1]
        tokens = build_tokens(("밥", Tag.일반명사))
        assert msg.render(tokens) == Tag.일반명사

    def test_dform_and_static_text_mixed(self):
        rules = rule().tag(Tag.일반명사).msg("[{dform[0]}] 검사").build()
        msg = rules[0][1]
        tokens = build_tokens(("밥", Tag.일반명사))
        assert msg.render(tokens) == "[밥] 검사"

    def test_dform_and_form_mixed(self):
        rules = (
            rule()
            .form("밥")
            .tag(Tag.일반명사)
            .msg("{form[0]} → {dform[1]}")
            .build()
        )
        msg = rules[0][1]
        tokens = build_tokens(("밥", Tag.일반명사), ("국", Tag.일반명사))
        assert msg.render(tokens) == "밥 → 국"


# ── build 출력 구조 ──

class TestBuildOutput:
    def test_returns_list(self):
        rules = rule().form("A").msg("x").build()
        assert isinstance(rules, list)
        assert len(rules) >= 1

    def test_each_rule_is_4_tuple(self):
        rules = rule().form("A").msg("x").build()
        for r in rules:
            assert len(r) == 4
            steps, msg, err_type, rule_id = r
            assert isinstance(steps, list)
            assert isinstance(msg, CompiledMessage)
            assert isinstance(err_type, SpellErrorType)
            assert isinstance(rule_id, str)

    def test_each_step_is_4_tuple(self):
        rules = rule().form("A").form("B").msg("x").build()
        for step in rules[0][0]:
            assert len(step) == 4
            cond, spacing, opt, ctx = step
            assert isinstance(spacing, SpacingRule)
            assert isinstance(opt, bool)
            assert isinstance(ctx, bool)

    def test_step_order_preserved(self):
        rules = rule().form("A").form("B").form("C").msg("x").build()
        steps = rules[0][0]
        assert steps[0][0].form == "A"
        assert steps[1][0].form == "B"
        assert steps[2][0].form == "C"

    def test_default_rule_id_is_empty(self):
        rules = rule().form("A").msg("x").build()
        assert rules[0][3] == ""


# ── error type / rule id ──

class TestErrorTypeAndId:
    def test_default_error_type_from_init(self):
        rules = rule().form("A").msg("x").build()
        assert rules[0][2] == SpellErrorType.TEST

    def test_errtype_overrides_init(self):
        rules = (
            RuleBuilder(SpellErrorType.TEST)
            .form("A")
            .msg("x")
            .errtype(SpellErrorType.NEED_ML_JUDGE)
            .id("R1")
            .build()
        )
        assert rules[0][2] == SpellErrorType.NEED_ML_JUDGE

    def test_id_sets_rule_id(self):
        rules = (
            RuleBuilder(SpellErrorType.NEED_ML_JUDGE)
            .form("A")
            .msg("x")
            .id("R-42")
            .build()
        )
        assert rules[0][3] == "R-42"


# ── 통합 (복합 시나리오) ──

class TestIntegratedScenarios:
    def test_full_chain_builds_successfully(self):
        rules = (
            rule()
            .form("A")
            .context()
            .tag(Tag.일반명사)
            .if_spaced()
            .form("B")
            .opt()
            .msg("test")
            .build()
        )
        assert len(rules) == 1
        steps = rules[0][0]
        assert len(steps) == 3
        # step 0: form A, context
        assert steps[0][0].form == "A"
        assert steps[0][3] is True
        # step 1: tag, spaced
        assert steps[1][1] == SpacingRule.SPACED
        # step 2: form B, opt
        assert steps[2][2] is True

    def test_and_or_not_mixed(self):
        rules = (
            rule()
            .AND(tag(Tag.일반명사), form("밥"))
            .OR(tag(Tag.숫자), form("0"))
            .NOT(form("X"))
            .msg("mixed")
            .build()
        )
        # AND(tag, form) → TagAndFormCondition 1개
        # OR(tag, form) → 같은 step 내 2개 조건 → product 2배
        # NOT → 1개
        # 총 1 × 2 × 1 = 2 규칙
        assert len(rules) == 2
        for r in rules:
            steps = r[0]
            assert isinstance(steps[0][0], TagAndFormCondition)
            assert isinstance(steps[2][0], NotCondition)