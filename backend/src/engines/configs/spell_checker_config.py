from src.engines.configs.spell_checker_config_builder import *
from src.models.interface import Tag, TagGroup, SpellErrorType
from src.engines.configs import spell_checker_config_meaning, spell_checker_config_spacing, spell_checker_config_specific, spell_checker_config_spelling, spell_checker_config_warning, spell_checker_config_complex, spell_checker_config_model

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

# TEST_SPELL_CHECK_RULES = [
#     *rule().id("NNB_데_동사")
#     .tag_form(Tag.의존명사, "데").if_not_spaced()
#     .tags({Tag.동사, Tag.동사규칙활용, Tag.동사불규칙활용})
#     .msg("{dtag[1]} / {dform[1]}").build(),

#     *rule().id("NNB_데_명사")
#     .tag_form(Tag.의존명사, "데").if_not_spaced()
#     .tag(Tag.일반명사)
#     .msg("{dtag[1]} / {dform[1]}").build(),   
# ]

TEST_SPELL_CHECK_RULES = [
    *rule().id("EC_면서_붙여쓰기")
    .tag_form(Tag.연결어미, "면서").if_spaced()
    .msg("'면서'를 앞 말에 붙여 써야 합니다.").build(),
]

ML_LABELINGS = [
]

SPELL_CHECK_RULES: list[KoSpellRules] = [
    *spell_checker_config_spacing.GENERAL_SPACING_ERRORS,
    *spell_checker_config_spacing.SPACING_ERRORS,
    *spell_checker_config_spelling.SPELL_MISS_ERRORS,
    *spell_checker_config_meaning.MEANING_CONFLICT_ERRORS,
    *spell_checker_config_specific.KIWI_EXCEPTION_ERRORS,
    *spell_checker_config_complex.COMPLEX_ERRORS,
    # *spell_checker_config_warning.WARNINGS,
 ]