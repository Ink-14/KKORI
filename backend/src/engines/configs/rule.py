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
    *rule().id("XSN_하다_붙여쓰기")
    .AND(tag(Tag.일반명사), forms(하다_MUST_ATTACHED)).context()
    .tag_form(Tag.동사파생접미사, "하").if_spaced()
    .msg("'하다'를 앞 말에 붙여 써야 합니다.").build(),
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