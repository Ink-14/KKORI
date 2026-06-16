from src.engines.configs.rule_builder import *
from src.models.interface import Tag, TagGroup, SpellErrorType

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
    *rule()
    .id("따라_붙여쓰기")
    .tags({Tag.일반명사}).context()
    .tag_form(Tag.동사, "따르").if_spaced()
    .tag_form(Tag.연결어미, "어")
    .msg("'따라'를 앞 말에 붙여 써야 합니다.").build(),
]