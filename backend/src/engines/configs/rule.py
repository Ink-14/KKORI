from src.engines.configs.rule_builder import *
from src.models.interface import Tag, TagGroup, SpellErrorType
from src.engines.configs import rule_meaning, rule_spacing, rule_specific, rule_spelling, rule_warning, rule_complex, rule_model

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
    *rule().id("REP_헤매다")
    .tag(Tag.일반명사)
    .tag_form(Tag.일반명사, "속").if_not_spaced()
    .msg("'헤매다'의 오타가 아닌가요?").build(),
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