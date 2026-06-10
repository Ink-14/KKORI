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

TEST_SPELL_CHECK_RULES = [
    *rule().id("MIF_되~")
    .AND(tags({Tag.동사, Tag.동사파생접미사}), form("되"))
    .AND(tag(Tag.연결어미), forms({"서"}))
    .msg("'돼{form[1]}'batchim(\"이\", \"가\") 올바른 표현입니다.").build(),
    
    *rule().id("MIF_되어")
    .AND(tags({Tag.동사, Tag.동사파생접미사}), form("되"))
    .tag_form(Tag.연결어미, "여")
    .msg("'되어'가 올바른 표현입니다.").build(),
    
    *rule().id("MIF_되며")
    .AND(tags({Tag.동사, Tag.동사파생접미사}), form("되"))
    .tag_form(Tag.연결어미, "으며")
    .msg("'되며'가 올바른 표현입니다.").build(),
    
    *rule().id("MIF_된")
    .AND(tags({Tag.동사, Tag.동사파생접미사}), form("되"))
    .tag_form(Tag.연결어미, "은")
    .msg("'된'이 올바른 표현입니다.").build(),
    
    *rule().id("MIF_되+연결어미")
    .AND(tags({Tag.동사, Tag.동사파생접미사}), form("되"))
    .tag_form(Tag.연결어미, "어")
    .tags(TagGroup.어미).if_not_spaced()
    .msg("'merge((\"되\", {dtag[0]}), ({dform[2]}, {dtag[2]}))'의 오타가 아닌가요?").build(),
    
    *rule().id("MIF_되어 있다")
    .AND(tags({Tag.동사, Tag.동사파생접미사}), form("되"))
    .tag_form(Tag.연결어미, "어")
    .tag_form(Tag.선어말어미, "었").if_spaced()
    .msg("'되어 있다'의 오타가 아닌가요?").build(),
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