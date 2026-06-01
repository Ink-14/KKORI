from src.engines.configs.spell_checker_config_builder import *
from src.models.interface import Tag, TagGroup, SpellErrorType
from src.engines.configs import spell_checker_config_meaning, spell_checker_config_spacing, spell_checker_config_specific, spell_checker_config_spelling, spell_checker_config_warning, spell_checker_config_complex

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

받다_ALLOWS = {"감동", "견제", "경례", "공격", "구원", "다운로드", "답변", "박수", "발급", "발주", "벌", "보고", "보답", "보상", "보호", "부여", "비난", "사랑", "사면", "상처", "선고", "선택", "선물", "세례", "수여", "수령", "신청", "습격", "오해", "양도", "억압", "열", "영향", "외면", "용서", "인계", "인도", "인정", "자극", "저주", "전달", "제공", "제안", "제재", "제한", "조명", "조사", "존경", "주목", "주문", "지원", "지적", "차별", "처벌", "초대", "축복", "축하", "충격", "치료", "치유", "칭송", "통보", "평가", "피해", "하사", "호평", "허락", "협박"}

TEST_SPELL_CHECK_RULES = [
    *rule()
    .AND(tag(Tag.일반명사), NOT(forms(받다_ALLOWS)))
    .tag_form(Tag.동사불규칙활용, "받").if_spaced()
    .msg("{dform[0]}").detail("물리적으로 전달받는 것이 아닌, 어떤 행위의 대상이 됨을 나타낼 때에는 '받다'를 앞 말에 붙여 써야 합니다.\n예를 들어 '평가받다'의 경우, '평가'라는 물건을 받는 것이 아닌 '평가를 당하다'의 의미이므로 '평가받다'로 붙여 씁니다.\n'받다'를 '하다'로 바꿔 써서 말이 된다면, 붙여 씁니다.\n※열받다는 예외적으로 붙여 씁니다.").build(),
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

    *rule()
    .id("걸_띄어쓰기")
    .tags({Tag.관형사형전성어미, Tag.관형사, Tag.관형격조사})
    .AND(tag(Tag.의존명사), forms({"거"})).if_not_spaced()
    .tag_form(Tag.목적격조사, "ᆯ")
    .msg("'걸'을 앞 말과 띄어 써야 합니다.").build(),
    
    *rule()
    .id("는데_띄어쓰기")
    .tag_form(Tag.관형사형전성어미, "는")
    .tag_form(Tag.의존명사, "데").if_not_spaced()
    .NOT(AND(tag(Tag.보조사), forms({"다", "다가"}))).context()
    .msg("'는 데'로 띄어 써야 합니다.").build(),
    
    *rule()
    .id("같이_붙여쓰기")
    .tags(TagGroup.체언)
    .tag(Tag.닫는부호).opt()
    .tag_form(Tag.일반부사, "같이").if_spaced()
    .msg("~처럼의 의미일 때는 '같이'를 붙여 써야 합니다.").build(),
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