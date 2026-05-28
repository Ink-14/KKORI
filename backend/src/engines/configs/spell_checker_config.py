from src.engines.configs.spell_checker_config_builder import *
from src.models.interface import Tag, TagGroup, SpellErrorType
from src.engines.configs import spell_checker_config_meaning, spell_checker_config_spacing, spell_checker_config_specific, spell_checker_config_spelling, spell_checker_config_warning, spell_checker_config_complex, spell_checker_config_model

# 규칙 작성 예시
def rule() -> RuleBuilder:
    return RuleBuilder(SpellErrorType.TEST)

SAMPLE = [
    *rule() # *rule()로 규칙 시작을 선언합니다.

    .tags({Tag.형용사, Tag.형용사불규칙활용}) # 체이닝으로 1개의 조건을 표현합니다.
    .tag_form(Tag.연결어미, "지").opt() # opt()로 '있어도 되고 없어도 되는' 조건을 표현합니다.
    .tag_form(Tag.보조용언, "않").if_not_spaced() # if_spaced() 또는 if_not_spaced()로 띄어쓰기 상태를 표현합니다.
    .form("는").context() # context()로 오류 표시 인덱스에는 표시되지 않지만, 규칙에는 포함되는 조건을 설정합니다. 

    # msg로 규칙이 매칭되었을 경우 보여줄 메시지를 설정할 수 있습니다.
    .msg("'merge(({dform[0]}, {dtag[0]}), (\"지\", \"연결어미\")) 않은'이 올바른 표현입니다.")
    
    .build(), # 모든 규칙은 build(),로 끝나야 합니다.
]

TEST_SPELL_CHECK_RULES = [
]

ML_TRAINED = spell_checker_config_model.ML_READY
ML_LABELINGS = spell_checker_config_model.ML_LABELINGS

SPELL_CHECK_RULES: list[KoSpellRules] = [
    *spell_checker_config_spacing.GENERAL_SPACING_ERRORS,
    *spell_checker_config_spacing.SPACING_ERRORS,
    *spell_checker_config_spelling.SPELL_MISS_ERRORS,
    *spell_checker_config_meaning.MEANING_CONFLICT_ERRORS,
    *spell_checker_config_specific.KIWI_EXCEPTION_ERRORS,
    *spell_checker_config_complex.COMPLEX_ERRORS,
    # *spell_checker_config_warning.WARNINGS,
 ]