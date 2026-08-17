from src.engines.configs.rule_builder import RuleBuilder, AND, OR, NOT, tag, tags, tag_form, form, forms, lemma, batchim, longer, SpacingRule, KoSpellRules
from src.models.interface import Tag, TagGroup, SpellErrorType
from src.engines.configs.rule_constants import 보조용언_FORMS, 피우다_TARGETS, 펴다_TARGETS

def rule() -> RuleBuilder:
    return RuleBuilder(SpellErrorType.COMPLEX)

_SPELLING_SPACING = [
    *rule().id("COMPLEX_@@년도")
    .tag(Tag.일반명사)
    .form("년도").if_not_spaced()
    .msg("'{dform[0]} 연도'가 올바른 표현입니다.").build(),

    *rule().id("COMPLEX_안주 거리")
    .tag_form(Tag.일반명사, "안주")
    .tag_form(Tag.의존명사, "거리").if_spaced()
    .msg("'안줏거리'가 올바른 표현입니다.").build(),

    *rule().id("COMPLEX_파투 나다")
    .tag_form(Tag.일반명사, "파토")
    .AND(tag(Tag.동사), forms({"나", "내"})).if_not_spaced()
    .msg("'파투 {form[1]}다'가 올바른 표현입니다.").build(),

    *rule().id("COMPLEX_흩트리+보조용언")
    .tag_form(Tag.동사, "흐트리")
    .tag(Tag.연결어미)
    .AND(tag(Tag.보조용언), forms(보조용언_FORMS)).if_not_spaced()
    .msg('\'흩트려 merge(({dform[2]}, "보조용언"), ("다", "종결어미"))\'가 올바른 표현입니다.').build(),

    *rule().id("COMPLEX_갖다 놓다+띄어쓰기")
    .tag_form(Tag.동사, "가")
    .tag_form(Tag.선어말어미, "었")
    .tag_form(Tag.연결어미, "다")
    .tag_form(Tag.보조용언, "놓").if_not_spaced()
    .msg("'갖다 놓다'로 써야 합니다.").build(),

    *rule().id("COMPLEX_때_오타+띄어쓰기")
    .NOT(tag_form(Tag.동사, "쓰"))
    .tag_form(Tag.관형사형전성어미, "ᆯ").if_not_spaced().context()
    .form("떄")
    .msg("'merge(({dform[0]}, {dtag[0]}), (\"ᆯ\", \"관형사형전성어미\")) 때'의 오타가 아닌가요?").build(),

    *rule().id("COMPLEX_쓸데_오타+띄어쓰기_1")
    .tag_form(Tag.동사, "쓰")
    .tag_form(Tag.관형사형전성어미, "ᆯ")
    .forms({"때", "떄"})
    .tag_form(Tag.형용사, "없").if_spaced()
    .msg("'쓸데없다'가 올바른 표현입니다.").build(),

    *rule().id("COMPLEX_쓸데_오타+띄어쓰기_1")
    .tag_form(Tag.동사, "쓰")
    .tag_form(Tag.관형사형전성어미, "ᆯ")
    .forms({"때", "떄"})
    .tag_form(Tag.일반부사, "없이").if_spaced()
    .msg("'쓸데없이'가 올바른 표현입니다.").build(),

    *rule().id("COMPLEX_뜬금_오타+띄어쓰기_1")
    .tag_form(Tag.일반명사, "뜬끔")
    .tag_form(Tag.형용사, "없").if_spaced()
    .msg("'뜬금'이 올바른 표현입니다. 또한 '뜬금없다'로 붙여 써야 합니다.").build(),

    *rule().id("COMPLEX_뜬금_오타+띄어쓰기_2")
    .tag_form(Tag.일반명사, "뜬끔")
    .tag_form(Tag.일반부사, "없이").if_spaced()
    .msg("'뜬금'이 올바른 표현입니다. 또한 '뜬금없이'로 붙여 써야 합니다.").build(),

    *rule().id("COMPLEX_피우다_오타+띄어쓰기_1")
    .AND(tag(Tag.일반명사), forms(피우다_TARGETS)).context()
    .tag_form(Tag.동사, "피").if_not_spaced()
    .msg("'{form[0]}batchim(\"을\", \"를\") 피우다'가 올바른 표현입니다. 또한 앞 말과 띄어 써야 합니다.").build(),
    
    *rule().id("COMPLEX_펴다_오타+띄어쓰기_1")
    .AND(tag(Tag.일반명사), forms(펴다_TARGETS)).context()
    .tag_form(Tag.동사, "피").if_not_spaced()
    .msg("'{form[0]}batchim(\"을\", \"를\") 펴다'가 올바른 표현입니다. 또한 앞 말과 띄어 써야 합니다.").build(),

    *rule().id("COMPLEX_별의별_오타+띄어쓰기")
    .tag_form(Tag.일반명사, "별")
    .tag_form(Tag.부사격조사, "에")
    .tag_form(Tag.관형사, "별")
    .msg("'별의별'이 올바른 표현입니다.").build(),
    
    *rule().id("COMPLEX_ㄴ다잖아_MIF+띄어쓰기")
    .tags(TagGroup.용언)
    .tag_form(Tag.관형사형전성어미, "ᆫ")
    .tag_form(Tag.의존명사, "대").if_spaced()
    .tag(Tag.긍정지정사)
    .tag_form(Tag.종결어미, "잖아")
    .msg("'merge(({dform[0]}, {dtag[0]}), (\"다\", \"연결어미\"))잖아'가 올바른 표현입니다.").build(),

    *rule().id("COMPLEX_쯤")
    .tag_form(Tag.일반명사, "때").context()
    .tag_form(Tag.의존명사, "즈음").if_spaced()
    .msg("'쯤'이 올바른 표현입니다. 또한 '쯤'을 앞 말에 붙여 써야 합니다.").build(),

    *rule().id("COMPLEX_선어말어미+을 게")
    .tag(Tag.선어말어미).context()
    .tag_form(Tag.종결어미, "을께")
    .msg("'게'가 올바른 표현입니다. 또한 '게'를 앞 말과 띄어 써야 합니다.").build(),
    
    *rule().id("COMPLEX_새어나가다 REP+띄어쓰기")
    .tag_form(Tag.동사, "세어나가")
    .msg("'새어 나가다'의 오타가 아닌가요?").build(),

    *rule().id("COMPLEX_쯤 REP+띄어쓰기")
    .tags({Tag.일반명사, Tag.의존명사, Tag.숫자, Tag.일련번호})
    .tag_form(Tag.일반명사, "쯔음").if_spaced()
    .msg("'쯤'이 올바른 표현입니다. 또한 앞 말과 붙여 써야 합니다.").build(),

    *rule().id("COMPLEX_즈음 REP+띄어쓰기")
    .tag(Tag.관형사형전성어미)
    .tag_form(Tag.일반명사, "쯔음").if_not_spaced()
    .msg("'즈음'이 올바른 표현입니다. 또한 앞 맢과 띄어 써야 합니다.").build(),
    
    *rule().id("COMPLEX_쳐들어가다 REP+띄어쓰기")
    .tag_form(Tag.동사, "처들")
    .tag_form(Tag.연결어미, "어")
    .tag_form(Tag.보조용언, "가").if_spaced()
    .msg("'쳐들어가다'로 써야 합니다.").build(),
    
    *rule().id("COMPLEX_~자 말자 MIF+띄어쓰기")
    .tag_form(Tag.일반부사, "다").context()
    .tags(TagGroup.용언)
    .tag_form(Tag.연결어미, "자")
    .tag_form(Tag.보조용언, "말").if_spaced()
    .tag_form(Tag.연결어미, "자")
    .msg("'merge(({dform[0]}, {dtag[0]}), (\"자마자\", \"연결어미\"))'의 오타가 아닌가요?").build(),

    *rule().id("COMPLEX_발 붙히다 MIF+띄어쓰기")
    .tag_form(Tag.일반명사, "발")
    .tag_form(Tag.동사, "붙히").if_spaced()
    .msg("'발붙이다'가 올바른 표현입니다.").build(),
    
    *rule().id("COMPLEX_오활용+오어미")
    .tag_form(Tag.동사, "치루")
    .AND(tag(Tag.연결어미), forms({"ᆯ려고", "ᆯ라고"}))
    .msg("'merge((\"치르\", \"동사\"), (\"려고\", \"연결어미\"))'가 올바른 표현입니다.").build(),
    
    *rule().id("COMPLEX_새어 나오다_REP+띄어쓰기").rank(1)
    .tag_form(Tag.동사, "세")
    .tag_form(Tag.연결어미, "어")
    .tag_form(Tag.동사, "나오").if_not_spaced()
    .msg("'새어 나오다'의 오타가 아닌가요?").build(),

    *rule().id("COMPLEX_체하다_REP+띄어쓰기")
    .tag(Tag.관형사형전성어미)
    .tag_form(Tag.의존명사, "채").if_not_spaced()
    .tag_form(Tag.동사, "하").if_not_spaced().context()
    .msg("'체하다'의 오타가 아닌가요? 또한 '체하다'든, '채'든 앞 말과 띄어 써야 합니다.").build(),
    
    *rule().id("COMPLEX_헤쳐 나가다 REP+띄어쓰기")
    .tag_form(Tag.동사, "해치")
    .tag_form(Tag.연결어미, "어")
    .tag_form(Tag.보조용언, "나가").if_not_spaced()
    .msg("'헤쳐 나가다'의 오타가 아닌가요?").build(),
]

COMPLEX_ERRORS: list[KoSpellRules] = [
    *_SPELLING_SPACING,
]