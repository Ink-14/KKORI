from src.engines.configs.rule_builder import *
from src.models.interface import Tag, TagGroup, SpellErrorType
from src.engines.configs import rule_meaning, rule_spacing, rule_specific, rule_spelling, rule_warning, rule_complex, rule_model
from src.engines.configs.rule_constants import *

# 규칙 작성 예시
def rule() -> RuleBuilder:
    return RuleBuilder(SpellErrorType.TEST)

SAMPLE = [
    *rule()
    .tags({Tag.형용사, Tag.형용사불규칙활용})
    .tag_form(Tag.연결어미, "지")
    .tag_form(Tag.보조용언, "않")
    .form("는")
    .msg("'merge(({dform[0]}, {dtag[0]}), (\"지\", \"연결어미\")) 않은'이 올바른 표현입니다.").build(),
]

TEST_SPELL_CHECK_RULES = [
    *rule().id("VV_함께하다_붙여쓰기")
    .AND(tag(Tag.부사격조사), forms({"와", "과"})).context()
    .tag(Tag.보조사).opt().context()
    .tag_form(Tag.일반부사, "함께")
    .tag_form(Tag.동사, "하").if_spaced()
    .msg("'함께하다'로 붙여 써야 합니다.").build(),
]

ML_LABELINGS = [
]

SPELL_CHECK_RULES: list[KoSpellRules] = [
    *rule_spacing.GENERAL_SPACING_ERRORS,
    *rule_spacing.SPACING_ERRORS,
    *rule_spelling.SPELL_MISS_ERRORS,
    *rule_meaning.MEANING_CONFLICT_ERRORS,
    *rule_specific.KIWI_EXCEPTION_ERRORS,
    *rule_complex.COMPLEX_ERRORS,
    # *rule_warning.WARNINGS,
 ]