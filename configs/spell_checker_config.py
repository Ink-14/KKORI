from korean_spell_checker.configs.spell_checker_config_builder import *
from korean_spell_checker.models.interface import Tag, TagGroup, SpellErrorType
from korean_spell_checker.configs import spell_checker_config_meaning, spell_checker_config_spacing, spell_checker_config_specific, spell_checker_config_spelling, spell_checker_config_warning

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

JOSA_TARGETS = {Tag.일반명사, Tag.고유명사}

TEST_SPELL_CHECK_RULES = [
    *rule()
    .id("JOSA_으로")
    .AND(tags(JOSA_TARGETS), OR(no_batchim(), batchim("ᆯ")))
    .tag_form(Tag.부사격조사, "으로")
    .msg('받침이 없거나 ㄹ로 끝나는 명사에는 \'로\'를 사용해야 합니다. \'merge(({dform[0]}, {dtag[0]}), ("로", "부사격조사"))\'의 오타가 아닌가요?').build(),

    *rule()
    .id("JOSA_로")
    .AND(tags(JOSA_TARGETS), AND(any_batchim(), NOT(batchim("ᆯ"))))
    .tag_form(Tag.부사격조사, "로")
    .msg('ㄹ이 아닌 받침으로 끝나는 명사에는 \'으로\'를 사용해야 합니다. \'merge(({dform[0]}, {dtag[0]}), ("으로", "부사격조사"))\'의 오타가 아닌가요?').build(),

    *rule()
    .id("JOSA_을")
    .AND(tags(JOSA_TARGETS), no_batchim())
    .tag_form(Tag.목적격조사, "을")
    .msg('받침 없는 명사에는 \'를\'을 사용해야 합니다. \'merge(({dform[0]}, {dtag[0]}), ("를", "목적격조사"))\'의 오타가 아닌가요?').build(),

    *rule()
    .id("JOSA_를")
    .AND(tags(JOSA_TARGETS), any_batchim())
    .tag_form(Tag.목적격조사, "를")
    .msg('받침 있는 명사에는 \'을\'을 사용해야 합니다. \'merge(({dform[0]}, {dtag[0]}), ("을", "목적격조사"))\'의 오타가 아닌가요?').build(),
]

def rule() -> RuleBuilder:
    return RuleBuilder(SpellErrorType.NEED_ML_JUDGE)

ML_READY = [    
    *rule()
    .id("던_든_오타")
    .tag_form(Tag.관형사형전성어미, "던")
    .msg("나열할 때는 '든'이 올바른 표현입니다.").build(),
    
    *rule()
    .id("던가_든가_오타")
    .form("라던가")
    .msg("나열할 때는 '라든가'가 올바른 표현입니다.").build(),
    
    *rule()
    .id("이라던가_라든가_오타")
    .form("이라던가")
    .msg("나열할 때는 '이라든가'가 올바른 표현입니다.").build(),
    
    *rule()
    .id("ㄴ다던가_ㄴ다든가_오타")
    .form("ᆫ다던가")
    .msg("나열할 때는 '~다던가'가 올바른 표현입니다.").build(),
    
    *rule()
    .id("다던가_다든가_오타")
    .form("다던가")
    .msg("나열할 때는 '~다던가'가 올바른 표현입니다.").build(),
    
    *rule()
    .id("는다던가_는다든가_오타")
    .form("는다던가")
    .msg("나열할 때는 '는다던가'가 올바른 표현입니다.").build(),
    
    *rule()
    .id("던지_든지_오타")
    .AND(tags({Tag.연결어미, Tag.종결어미, Tag.보조사}), form("던지"))
    .msg("나열할 때는 '든지'가 올바른 표현입니다.").build(),
]

ML_TRAINED = [
    *rule()
    .id("지_띄어쓰기")
    .AND(tags({Tag.의존명사, Tag.대명사}), form("지")).if_spaced()
    .msg("'지'를 붙여 써야 합니다.").build(),
    
    *rule()
    .id("같이_붙여쓰기")
    .tags({Tag.일반명사, Tag.고유명사, Tag.명사형전성어미, Tag.명사파생접미사, Tag.대명사, Tag.숫자, Tag.알파벳}).context()
    .form("같이").if_spaced()
    .msg("~처럼의 의미일 때는 '같이'를 붙여 써야 합니다.").build(),
    
    *rule()
    .id("따라_붙여쓰기")
    .tags({Tag.일반명사}).context()
    .tag_form(Tag.동사, "따르").if_spaced()
    .tag_form(Tag.연결어미, "어")
    .msg("'따라'를 앞 말에 붙여 써야 합니다.").build(),
    
    *rule()
    .id("던지_든지_오타")
    .AND(tags({Tag.연결어미, Tag.종결어미, Tag.보조사}), form("던지"))
    .msg("나열할 때는 '든지'가 올바른 표현입니다.").build(),
]

ML_LABELINGS = [
    
]

SPELL_CHECK_RULES: list[KoSpellRules] = [
    *spell_checker_config_spacing.GENERAL_SPACING_ERRORS,
    *spell_checker_config_spacing.SPACING_ERRORS,
    *spell_checker_config_spelling.SPELL_MISS_ERRORS,
    *spell_checker_config_meaning.MEANING_CONFLICT_ERRORS,
    # *spell_checker_config_warning.WARNINGS,
    *spell_checker_config_specific.KIWI_EXCEPTION_ERRORS
 ]