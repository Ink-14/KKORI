from korean_spell_checker.configs.spell_checker_config_builder import *
from korean_spell_checker.models.interface import Tag, TagGroup, SpellErrorType
from korean_spell_checker.configs import spell_checker_config_meaning, spell_checker_config_spacing, spell_checker_config_specific, spell_checker_config_spelling, spell_checker_config_warning

# 규칙 작성 예시
def rule() -> RuleBuilder:
    return RuleBuilder(SpellErrorType.TEST)

TEST_SPELL_CHECK_RULES = [
    *rule()
    .tags({Tag.형용사, Tag.형용사불규칙활용})
    .tag_form(Tag.연결어미, "지")
    .tag_form(Tag.보조용언, "않")
    .form("는")
    .msg("'merge(({dform[0]}, {dtag[0]}), (\"지\", \"연결어미\")) 않은'이 올바른 표현입니다.").build(),
    
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

def rule() -> RuleBuilder:
    return RuleBuilder(SpellErrorType.NEED_ML_JUDGE)

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
    *rule()
    .id("예요_오타")
    .AND(tags({Tag.일반명사, Tag.의존명사, Tag.고유명사, Tag.명사파생접미사, Tag.명사형전성어미}), NOT(any_batchim()))
    .tag_form(Tag.긍정지정사, "이").opt()
    .tag_form(Tag.종결어미, "에요")
    .msg("'{dform[0]}예요'가 올바른 표현입니다.").build(),
]

SPELL_CHECK_RULES: list[KoSpellRules] = [
    *spell_checker_config_spacing.GENERAL_SPACING_ERRORS,
    *spell_checker_config_spacing.SPACING_ERRORS,
    *spell_checker_config_spelling.SPELL_MISS_ERRORS,
    *spell_checker_config_meaning.MEANING_CONFLICT_ERRORS,
    # *spell_checker_config_warning.WARNINGS,
    *spell_checker_config_specific.KIWI_EXCEPTION_ERRORS
 ]