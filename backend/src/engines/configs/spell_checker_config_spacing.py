from src.engines.configs.spell_checker_config_builder import *
from src.models.interface import Tag, TagGroup, SpellErrorType

NUMBER_DETERMINERS = {"첫", "두", "세", "네", "다섯", "여섯", "일곱", "여덟", "아홉", "열", "백", "천", "만", "억"}
MONEY_DETERMINERS = {"골드", "엔", "원", "다이아"}
되다_EXCEPTIONS = {"얼마", "말", "기회", "부자", "배", "숙부", "여행", "형", "언니", "누나", "엄마", "아빠", "삼촌", "이모", "고모", "남편", "아내", "이튿날", "정도", "축제", "여정", "시간", "때", "돈", "습관", "파뿌리", "상태", "말동무", "후반부", "습관", "아미타불", "나중", "팬", "한참", "달", "이상", "한참", "대명사", "쯤", "구슬", "꼴찌", "연휴", "하루", "며칠", "불기둥", "실세", "아이", "이득", "친구", "타임", "배우", "가량", "경기", "비서실장", "설상가상", "넘버원", "약", "새사람", "피범벅", "배심원"}
받다_ALLOWS = {"감동", "검사", "견제", "경고", "경례", "계승", "공격", "과대평가", "교육", "구원", "구박", "내정", "냉대", "다운", "다운로드", "답변", "대우", "면제", "멸시", "발급", "발령", "발주", "방해", "배정", "벌", "보고", "보급", "보답", "보상", "보호", "부여", "분배", "분양", "비난", "비판", "사랑", "사면", "상처", "선고", "선택", "선물", "세례", "수여", "수령", "수리", "수업", "수혈", "신청", "승인", "신임", "습격", "악수", "양도", "억압", "열", "영향", "오해", "외면", "용서", "인계", "인도", "인정", "자극", "저주", "전달", "제공", "제안", "제재", "제한", "조명", "조사", "존경", "주목", "주문", "지원", "지적", "차별", "처벌", "초대", "추천", "축복", "축하", "충격", "치료", "치유", "칭송", "통보", "평가", "피해", "하달", "하사", "호평", "허락", "협박"}
받다_DENYS = {"관심", "도움", "동정", "만점", "미움", "보살핌", "부케"}

def rule() -> RuleBuilder: # type: ignore
    return RuleBuilder(SpellErrorType.SPACING)

def word_3(word1: str, tag1: Tag, word2: str, tag2: Tag, word3: str, tag3: Tag, spacing_rule: SpacingRule, message: str):
    rule = RuleBuilder(SpellErrorType.SPACING).tag_form(tag1, word1).tag_form(tag2, word2).tag_form(tag3, word3)

    if spacing_rule == SpacingRule.SPACED:
        return rule.if_not_spaced().msg(f"'{message}'batchim(\"으로\",\"로\") 띄어 써야 합니다.").build()
    elif spacing_rule == SpacingRule.ATTACHED:
        return rule.if_spaced().msg(f"'{message}'batchim(\"으로\",\"로\") 붙여 써야 합니다.").build()
    elif spacing_rule == SpacingRule.ANY:
        raise ValueError("'Any' spacing rule is not allowed in word_3.")

def NNG_and_NNG(nng1: str, nng2: str, spacing_rule: SpacingRule, message = None) -> list[KoSpellRules]:
    rule = RuleBuilder(SpellErrorType.SPACING).tag_form(Tag.일반명사, nng1).tag_form(Tag.일반명사, nng2)
    
    if spacing_rule == SpacingRule.SPACED:
        rule.if_not_spaced()
        if message is None:
            message = "'{form[0]} {form[1]}'batchim(\"으로\",\"로\") 띄어 써야 합니다."
    elif spacing_rule == SpacingRule.ATTACHED:
        rule.if_spaced()
        if message is None:
            message = "'{form[0]}{form[1]}'batchim(\"으로\",\"로\") 붙여 써야 합니다."
    elif spacing_rule == SpacingRule.ANY:
        if message is None:
            raise ValueError("you must set error message to function 'NNG_and_NNG' if spacing rule is SpacingRule.ANY.")
        
    return rule.msg(message).build()
    
def NNG_and_some(nng: str, some: str, tag: str, spacing_rule: SpacingRule, message = None) -> list[KoSpellRules]:
    rule = RuleBuilder(SpellErrorType.SPACING).tag_form(Tag.일반명사, nng).tag_form(Tag[tag], some)
    
    message = f"merge((\"{some}\", \"{tag}\"), (\"다\", \"연결어미\"))"
    if spacing_rule == SpacingRule.SPACED:
        message = "{form[0]} " + message
        return rule.if_not_spaced().msg(f"'{message}'로 띄어 써야 합니다.").build()
    elif spacing_rule == SpacingRule.ATTACHED:
        message = "{form[0]}" + message
        return rule.if_spaced().msg(f"'{message}'로 붙여 써야 합니다.").build()
    elif spacing_rule == SpacingRule.ANY:
        if message is None:
            raise ValueError("you must set error message to function 'NNG_and_some' if spacing rule is SpacingRule.ANY.")
        return rule.msg(message).build()
    
def VV_EC_VV(vv1: tuple[str, str], ec: str, vv2: tuple[str, str], spacing_rule: SpacingRule, message = None, detail = None) -> list[KoSpellRules]:
    vv1_form, vv1_tag = vv1
    vv2_form, vv2_tag = vv2
    rule = RuleBuilder(SpellErrorType.SPACING).tag_form(Tag[vv1_tag], vv1_form).tag_form(Tag.연결어미, ec).tag_form(Tag[vv2_tag], vv2_form)

    message1 = f"merge((\"{vv1_form}\", \"{vv1_tag}\"), (\"{ec}\", \"연결어미\"))"
    message2 = f"merge((\"{vv2_form}\", \"{vv2_tag}\"), (\"다\", \"연결어미\"))"
    
    if spacing_rule == SpacingRule.SPACED:
        rule.if_not_spaced().msg(f"'{message1} {message2}'로 띄어 써야 합니다.")
    elif spacing_rule == SpacingRule.ATTACHED:
        rule.if_spaced().msg(f"'{message1}{message2}'로 붙여 써야 합니다.")
    elif spacing_rule == SpacingRule.ANY:
        if message is None:
            raise ValueError("you must set error message to function 'NNG_and_some' if spacing rule is SpacingRule.ANY.")
        rule.msg(message)

    if detail:
        rule.detail(detail)

    return rule.build()

GENERAL_SPACING_ERRORS: list[KoSpellRules] = [
    *rule()
    .id("되다_붙여쓰기")
    .NOT(tag(Tag.관형사형전성어미)).context()
    .AND(tag(Tag.일반명사), NOT(forms(되다_EXCEPTIONS)))
    .tag_form(Tag.동사, "되").if_spaced()
    .AND(NOT(tag_form(Tag.선어말어미, "시")), NOT(tag_form(Tag.의존명사, "자"))).context()
    .msg("'{dform[0]}되다'로 붙여 써야 합니다.").build(),
    
    *rule()
    .id("되다_관형사뒤_띄어쓰기")
    .tag(Tag.관형사형전성어미).context()
    .AND(tag(Tag.일반명사), NOT(forms(되다_EXCEPTIONS)))
    .tag_form(Tag.동사, "되").if_not_spaced()
    .NOT(tag_form(Tag.선어말어미, "시")).context()
    .msg("'{dform[0]}'batchim(\"을\", \"를\") 꾸미는 말이 있으므로 '{dform[0]} 되다'로 띄어 써야 합니다.").build(),

    *rule()
    .id("GENERAL_되다_예외들_띄어쓰기")
    .AND(tag(Tag.일반명사), forms(되다_EXCEPTIONS))
    .tag_form(Tag.동사, "되").if_not_spaced()
    .msg("'{dform[0]} 되다'로 띄어 써야 합니다.").build(),

    *rule()
    .tag(Tag.일반명사)
    .tag_form(Tag.동사파생접미사, "되").if_spaced()
    .msg("'되다'를 앞 말에 붙여 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.명사파생접미사, "화")
    .tag_form(Tag.동사, "되").if_spaced()
    .msg("'되다'를 앞 말에 붙여 써야 합니다.").build(),

    *rule()
    .NOT(tags({Tag.관형사, Tag.관형사형전성어미, Tag.형용사파생접미사, Tag.관형격조사, Tag.일반명사})).context()
    .tag(Tag.일반명사)
    .tag_form(Tag.동사파생접미사, "하").if_spaced()
    .msg("'하다'를 앞 말에 붙여 써야 합니다. '역할을 맡다'일 경우 띄어 써 주세요.").build(),

    *rule()
    .AND(tag(Tag.일반명사), longer(3))
    .tag_form(Tag.동사, "하").if_spaced()
    .msg("'하다'를 앞 말에 붙여 써야 합니다. '역할을 맡다'일 경우 띄어 써 주세요.").build(),
    
    *rule()
    .tag(Tag.체언접두사)
    .tag(Tag.일반명사)
    .AND(tags({Tag.동사, Tag.형용사파생접미사}), form("하")).if_spaced()
    .msg("'{dform[0]}{dform[1]}하다'로 붙여 써야 합니다.").build(),

    *rule()
    .tag(Tag.일반명사).context()
    .tag(Tag.보조사).context()
    .tag_form(Tag.동사, "하").if_not_spaced()
    .msg("'하다'를 앞 말과 띄어 써야 합니다.").build(),

    *rule()
    .tags({Tag.일반명사, Tag.대명사, Tag.고유명사})
    .tag(Tag.수사).if_not_spaced()
    .msg("수사 앞은 띄어 써야 합니다.").build(),

    *rule()
    .tags({Tag.일반명사, Tag.대명사}).context()
    .tag(Tag.관형사).if_not_spaced()
    .msg("관형사 앞을 띄어 써야 합니다.").build(),

    *rule()
    .NOT(tag(Tag.숫자)).context()
    .tag_form(Tag.구분부호, ",")
    .NOT(tags({Tag.숫자, Tag.닫는부호, Tag.구분부호, Tag.종결부호})).if_not_spaced()
    .msg("쉼표 뒤에 띄어쓰기가 없습니다.").build(),

    *rule()
    .tag(Tag.보격조사)
    .tag_form(Tag.동사, "되").if_not_spaced()
    .msg("'되다'를 띄어 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.일반부사, "안")
    .tag(Tag.형용사).if_not_spaced()
    .msg("'안' 뒤를 띄어 써야 합니다.").build(),
    
    *rule()
    .id("GENERAL_안_동사_띄어쓰기")
    .tag_form(Tag.일반부사, "안")
    .AND(NOT(form("되")), tags({Tag.동사, Tag.동사불규칙활용, Tag.동사규칙활용})).if_not_spaced()
    .msg('\'안 merge(({dform[1]}, {dtag[1]}), ("다", "종결어미"))\'로 띄어 써야 합니다.').build(),
    
    *rule()
    .tag_form(Tag.연결어미, "어야")
    .tag_form(Tag.선어말어미, "겠").if_spaced()
    .msg("'~야겠다'로 붙여 써야 합니다.").build(),
    
    *rule()
    .id("명사파생접미사_되다_붙여쓰기")
    .AND(tag(Tag.명사파생접미사), forms({"화", "시"}))
    .AND(tags({Tag.동사파생접미사, Tag.동사}), form("되")).if_spaced()
    .msg("'되다'를 앞 말에 붙여 써야 합니다.").build(),

    *rule()
    .tag(Tag.일반부사)
    .tag(Tag.보조용언).if_not_spaced()
    .msg('\'merge(({dform[1]}, "보조용언"), ("다", "종결어미"))\'를 앞 말과 띄어 써야 합니다.').build(),

    *rule()
    .tag(Tag.관형사형전성어미)
    .tags({Tag.일반명사, Tag.고유명사}).if_not_spaced()
    .tag(Tag.주격조사).context()
    .msg("명사 '{dform[1]}'batchim(\"을\", \"를\") 앞 말과 띄어 써야 합니다.").build(),

    *rule()
    .AND(tag(Tag.목적격조사), forms({"을", "를"}))
    .tags({Tag.동사, Tag.동사불규칙활용, Tag.동사규칙활용}).if_not_spaced()
    .msg("조사 '{form[0]}'batchim(\"과\", \"와\") 동사 'merge(({dform[1]}, {dtag[1]}), (\"다\", \"종결어미\"))'를 띄어 써야 합니다.").build(),

    *rule()
    .tag(Tag.연결어미).context()
    .AND(NOT(form("하")), tags({Tag.동사, Tag.동사규칙활용, Tag.동사불규칙활용})).if_not_spaced()
    .msg('\'merge(({dform[0]}, {dtag[0]}), ("다", "종결어미"))\'를 앞 말과 띄어 써야 합니다.').build(),
]

_SPACING_ERRORS = [
    *rule()
    .NOT(form("다시")).context()
    .tag_form(Tag.관형사, "한")
    .tag_form(Tag.의존명사, "번").if_not_spaced()
    .AND(tags(TagGroup.조사), NOT(form("은"))).if_not_spaced()
    .msg("'한 번'으로 띄어 써야 합니다.").build(),

    # *rule()
    # .tag(Tag.숫자)
    # .tag(Tag.수사)
    # .opt()
    # .forms(MONEY_DETERMINERS)
    # .if_not_spaced()
    # .msg("통화 단위를 띄어 써야 합니다.")
    # .build(),

    *rule()
    .tag(Tag.숫자)
    .tag_form(Tag.의존명사, "년")
    .AND(tag(Tag.일반명사), forms({"후", "뒤"})).if_not_spaced()
    .msg("'{dform[0]}년 {dform[2]}'로 띄어 써야 합니다.").build(),

    *rule()
    .tag(Tag.숫자).context()
    .tag(Tag.의존명사)
    .tag_form(Tag.의존명사, "차").if_not_spaced()
    .msg("기간을 나타내는 '{dform[0]}'batchim(\"과\", \"와\") '차'를 띄어 써야 합니다.").build(),

    *rule()
    .tags(TagGroup.체언)
    .form("시간").if_not_spaced()
    .msg("'{dform[0]} 시간'으로 띄어 써야 합니다.").build(),

    *rule()
    .tags({Tag.의존명사, Tag.일반명사, Tag.명사파생접미사, Tag.대명사})
    .form("뿐").if_spaced()
    .msg("'뿐'을 앞 말에 붙여 써야 합니다.").build(),
    
    *rule()
    .tags({Tag.관형사형전성어미})
    .form("뿐").if_not_spaced()
    .NOT(form("더러")).context()
    .msg("'뿐'을 앞 말과 띄어 써야 합니다.").build(),

    *rule()
    .AND(tag(Tag.관형사형전성어미), batchim("ᆯ"))
    .tag_form(Tag.의존명사, "뿐").if_spaced()
    .tag_form(Tag.부사격조사, "더러").if_not_spaced() # '뿐더러'의 형태만 찾도록 붙여 썼을 때만 OK
    .msg("'-ᆯ뿐더러'는 앞 말에 붙여 써야 합니다.").build(),

    *rule()
    .id("지_1_붙여쓰기")
    .AND(tag(Tag.관형사형전성어미), forms({"ᆯ", "는", "을"}))
    .AND(tags({Tag.일반명사, Tag.의존명사, Tag.대명사}), form("지")).if_spaced()
    .NOT(tag(Tag.명사파생접미사)).context()
    .msg("'지'를 앞 말과 붙여 써야 합니다.").build(),

    *rule()
    .id("지_2_붙여쓰기")
    .tag(Tag.일반명사).context()
    .tag(Tag.긍정지정사).context()
    .tag_form(Tag.관형사형전성어미, "ᆫ").context()
    .tag_form(Tag.의존명사, "지").if_spaced()
    .msg("'지'를 앞 말과 붙여 써야 합니다.").build(),
    
    *rule()
    .id("지_1_띄어쓰기")
    .tag_form(Tag.관형사형전성어미, "ᆫ")
    .AND(tags({Tag.의존명사, Tag.대명사}), form("지")).if_not_spaced()
    .tags(TagGroup.조사).context()
    .tag(Tag.숫자).context()
    .msg("시간의 흐름을 나타내는 경우, '지'를 앞 말과 띄어 써야 합니다.").build(),

    *rule()
    .id("지_2_띄어쓰기")
    .tag_form(Tag.관형사형전성어미, "ᆫ")
    .AND(tags({Tag.의존명사, Tag.대명사}), form("지")).if_not_spaced()
    .tag(Tag.숫자).context()
    .msg("시간의 흐름을 나타내는 경우, '지'를 앞 말과 띄어 써야 합니다.").build(),

    *rule()
    .id("지_3_띄어쓰기")
    .AND(tags({Tag.의존명사, Tag.대명사}), form("지")).if_not_spaced()
    .tag(Tag.보조사).opt().context()
    .tag(Tag.관형사).context()
    .msg("시간의 흐름을 나타내는 경우, '지'를 앞 말과 띄어 써야 합니다.").build(),
    
    *rule()
    .tag(Tag.관형사형전성어미).context()
    .tag_form(Tag.의존명사, "것")
    .tag_form(Tag.부사격조사, "보다").if_spaced()
    .msg("'것보다'로 붙여 써야 합니다.").build(),

    *rule()
    .tags({Tag.일반명사, Tag.대명사, Tag.고유명사})
    .tag_form(Tag.보조사, "대로").if_spaced()
    .msg("'대로'를 앞 말에 붙여 써야 합니다.").build(),

    *rule()
    .tags({Tag.일반명사})
    .tag_form(Tag.일반부사, "못").if_not_spaced()
    .tag_form(Tag.동사, "하")
    .msg("'{dform[0]} 못하다'로 띄어 써야 합니다.")
    .build(),

    *rule()
    .id("VV_지 못하다 이외_못 하다_띄어쓰기")
    .AND(NOT(tag_form(Tag.연결어미, "지")), NOT(tag(Tag.일반부사))).context()
    .AND(AND(AND(NOT(tag_form(Tag.연결어미, "지")), NOT(tag_form(Tag.목적격조사, "ᆯ"))), NOT(tags({Tag.일반부사, Tag.일반명사}))), NOT(tag_form(Tag.연결어미, "도"))).context()
    .tag_form(Tag.일반부사, "못")
    .tag_form(Tag.동사, "하").if_not_spaced()
    .msg("'못 하다'로 띄어 써야 합니다.")
    .detail("'못 하다'로 띄어 쓰는 경우는 행위가 불가능함을 나타낼 때 띄어 써야 합니다. '못하다'로 붙여 쓰는 경우는 가능하지만 잘하지는 못할 때 붙여 써야 합니다.\n\n예를 들어, '수영을 못 하다'는 수영을 아예 할 수 없는 경우를 지칭합니다. '수영을 못하다'는 할 수는 있으나 실력이 뛰어나지는 않을 때를 지칭합니다.")
    .build(),

    *rule()
    .id("VV_명사_못 하다_띄어쓰기")
    .tag(Tag.일반명사).context()
    .tag_form(Tag.일반부사, "못")
    .tag_form(Tag.동사, "하").if_not_spaced()
    .msg("'못 하다'로 띄어 써야 합니다.")
    .detail("'못 하다'로 띄어 쓰는 경우는 행위가 불가능함을 나타낼 때 띄어 써야 합니다. '못하다'로 붙여 쓰는 경우는 가능하지만 잘하지는 못할 때 붙여 써야 합니다.\n\n예를 들어, '수영을 못 하다'는 수영을 아예 할 수 없는 경우를 지칭합니다. '수영을 못하다'는 할 수는 있으나 실력이 뛰어나지는 않을 때를 지칭합니다.")
    .build(),

    *rule()
    .tag(Tag.일반명사)
    .tag_form(Tag.일반명사, "순").if_spaced()
    .msg("순서를 나타낼 경우 '날짜순으로'와 같이 붙여 써야 합니다.").build(),

    *rule()
    .tag(Tag.일반명사)
    .tag_form(Tag.의존명사, "순").if_spaced()
    .msg("순서를 나타낼 경우 '날짜순으로'와 같이 붙여 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.일반부사, "어서")
    .tag_form(Tag.동사, "오").if_not_spaced()
    .msg("'어서 오세요'로 띄어 써야 합니다.").build(),

    *rule()
    .tag_form(Tag.일반명사, "시간")
    .tag_form(Tag.일반명사, "문제").if_spaced()
    .tags({Tag.긍정지정사, Tag.종결어미}).context()
    .msg("'시간문제'로 붙여 써야 합니다.").build(),

    *rule()
    .tag_form(Tag.동사, "바라")
    .any()
    .tag_form(Tag.동사, "보").if_spaced()
    .msg("'바라보다'로 붙여 써야 합니다.").build(),

    *rule()
    .tag_form(Tag.일반명사, "주의")
    .tag_form(Tag.형용사, "깊").if_not_spaced()
    .msg("'주의 깊다'로 띄어 써야 합니다.").build(),

    *rule()
    .tag_form(Tag.일반명사, "욕심")
    .tag_form(Tag.동사, "부리").if_spaced()
    .msg("'욕심부리다'로 붙여 써야 합니다.").build(),

    *rule()
    .tag_form(Tag.일반명사, "기억")
    .tag_form(Tag.동사, "나").if_spaced()
    .msg("'기억나다'로 붙여 써야 합니다.").build(),

    *rule()
    .tag_form(Tag.일반부사, "그만")
    .tag_form(Tag.동사, "두").if_spaced()
    .msg("'멈추다'의 의미일 경우, '그만두다'로 붙여 써야 합니다.").build(),

    *rule()
    .tag_form(Tag.동사, "들리")
    .tag_form(Tag.연결어미, "어")
    .tag_form(Tag.보조용언, "주").if_spaced()
    .msg("'들려주다'로 붙여 써야 합니다.").build(),

    *rule()
    .tag_form(Tag.명사파생접미사, "씩").if_spaced()
    .msg("'씩'을 앞 말에 붙여 써야 합니다.").build(),

    *rule()
    .tag_form(Tag.의존명사, "듯")
    .tag_form(Tag.형용사파생접미사, "하").if_spaced()
    .msg("'듯하다'로 붙여 써야 합니다.").build(),

    *rule()
    .tag_form(Tag.의존명사, "듯")
    .tag_form(Tag.동사, "하").if_spaced()
    .msg("'듯하다'로 붙여 써야 합니다.").build(),

    *rule()
    .tag_form(Tag.동사, "끊이")
    .tag_form(Tag.명사형전성어미, "ᆷ")
    .OR(tag_form(Tag.형용사, "없"), tag_form(Tag.일반부사, "없이")).if_spaced()
    .msg("'끊임없다'로 붙여 써야 합니다.").build(),

    *rule()
    .tag_form(Tag.일반명사, "비")
    .AND(tag_form(Tag.동사, "오"), tag_form(Tag.동사, "내리"))
    .msg("'비 오다', '비 내리다'로 띄어 써야 합니다.").build(),

    *rule()
    .tag_form(Tag.동사, "주")
    .any()
    .tag_form(Tag.동사불규칙활용, "받").if_spaced()
    .msg("'주고받다'로 붙여 써야 합니다.").build(),

    *rule()
    .tags({Tag.어근, Tag.일반명사})
    .tag_form(Tag.형용사파생접미사, "하")
    .tag_form(Tag.연결어미, "어")
    .tag_form(Tag.보조용언, "하").if_spaced()
    .msg("'{dform[0]}해하다'로 붙여 써야 합니다.").build(),

    *rule()
    .tags({Tag.동사, Tag.형용사, Tag.형용사불규칙활용, Tag.형용사규칙활용, Tag.형용사파생접미사, Tag.형용사파생접미사규칙활용, Tag.형용사파생접미사불규칙활용})
    .tag_form(Tag.연결어미, "어")
    .tag_form(Tag.보조용언, "지").if_spaced()
    .msg("'지다'를 앞 말에 붙여 써야 합니다.").build(),
    
    *rule()
    .AND(tag(Tag.동사), forms({"갖", "바래"}))
    .tag_form(Tag.연결어미, "다")
    .AND(tag(Tag.보조용언), forms({"주", "드리"})).if_spaced()
    .msg("'merge(({form[0]}, \"동사\"), (\"다\", \"연결어미\")){form[2]}다'로 붙여 써야 합니다.").build(),

    *rule()
    .AND(tag(Tag.동사), forms({"가지", "모시", "데리"}))
    .tag_form(Tag.연결어미, "어다")
    .AND(tag(Tag.보조용언), forms({"주", "드리"})).if_spaced()
    .msg("'merge(({form[0]}, \"동사\"), (\"어다\", \"연결어미\")){form[2]}다'로 붙여 써야 합니다.").build(),

    *rule()
    .tag_form(Tag.일반부사, "안절부절")
    .tag_form(Tag.일반부사, "못").if_spaced()
    .tag_form(Tag.동사, "하")
    .msg("'안절부절못하다'로 붙여 써야 합니다.").build(),

    *rule()
    .tag_form(Tag.일반부사, "안절부절")
    .tag_form(Tag.일반부사, "못")
    .tag_form(Tag.동사, "하").if_spaced()
    .msg("'안절부절못하다'로 붙여 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.감탄사, "아참")
    .msg("'아 참'으로 띄어 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.감탄사, "거")
    .tag_form(Tag.감탄사, "참").if_spaced()
    .msg("'거참'으로 붙여 써야 합니다.").build(),
    
    *rule()
    .AND(tag(Tag.대명사), forms({"그것", "그거"}))
    .tag_form(Tag.일반부사, "참").if_spaced()
    .msg("'그것참'으로 붙여 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.체언접두사, "제")
    .OR(tag(Tag.숫자), tag(Tag.수사)).if_spaced()
    .NOT(tags({Tag.긍정지정사, Tag.알파벳, Tag.여는부호}))
    .msg("순서를 나타낼 때는 '제1회'와 같이 숫자를 앞 말에 붙여 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.체언접두사, "초")
    .any().if_spaced()
    .msg("'초(超)-'는 접두사이므로 뒤에 오는 말과 붙여 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.체언접두사, "폐")
    .any().if_spaced()
    .msg("'초(超)-'는 접두사이므로 뒤에 오는 말과 붙여 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.명사파생접미사, "상").if_spaced()
    .msg("위치 관계를 나타낼 경우 '네트워크상에'와 같이 붙여 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.명사파생접미사, "계").if_spaced()
    .msg("분야/영역의 의미인 경우, '계'를 앞 말에 붙여 써야 합니다. (예시: 연예계)").build(),
    
    *rule()
    .forms({"아르바이트", "회", "알바"})
    .form("비").if_spaced()
    .msg("'비용'의 뜻인 경우, '{form[0]}비'로 붙여 씁니다.").build(),
    
    *rule()
    .forms({"확인", "휴식", "관광", "격려", "연구", "답례", "응원"})
    .form("차").if_spaced()
    .msg("'{form[0]}차'로 붙여 써야 합니다.").build(),
    
    *rule()
    .form("어치").if_spaced()
    .msg("'만 원어치'처럼 '어치'를 앞 말에 붙여 써야 합니다.").build(),
    
    *rule()
    .form("짜리").if_spaced()
    .msg("'만 원짜리'처럼 '짜리'를 앞 말에 붙여 써야 합니다.").build(),
    
    *rule()
    .form("투성이").if_spaced()
    .msg("'-투성이'는 접미사이므로 앞 말과 붙여 써야 합니다.").build(),
    
    *rule()
    .id("거리다_XSV_붙여쓰기")
    .any()
    .tag_form(Tag.동사파생접미사, "거리").if_spaced()
    .msg("'{dform[0]}거리다'로 붙여 써야 합니다.").build(),
    
    *rule()
    .id("거리다_VV_붙여쓰기")
    .tags({Tag.일반명사, Tag.어근})
    .tag_form(Tag.동사, "거리").if_spaced()
    .msg("'{dform[0]}거리다'로 붙여 써야 합니다.").build(),

    *rule()
    .id("거리다_MAG_붙여쓰기")
    .AND(tag(Tag.일반부사), NOT(forms({"두근두근", "중얼중얼", "바들바들"})))
    .tag_form(Tag.동사, "거리").if_spaced()
    .msg("'{dform[0]}거리다'로 붙여 써야 합니다.").build(),
    
    *rule()
    .tags(TagGroup.체언)
    .tag_form(Tag.일반명사, "하").if_spaced()
    .tag_form(Tag.부사격조사, "에")
    .msg("'~의 아래'의 의미라면, '{dform[0]}하'로 붙여 써야 합니다. (예시: 그렇다는 전제하에)").build(),
    
    *rule()
    .any()
    .form("커녕").if_spaced()
    .msg("'커녕'을 앞 말에 붙여 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.의존명사, "뻔")
    .tag_form(Tag.형용사파생접미사, "하").if_spaced()
    .msg("'뻔하다'로 붙여 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.의존명사, "체")
    .tag_form(Tag.동사파생접미사, "하").if_spaced()
    .msg("'체하다'로 붙여 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.의존명사, "척")
    .AND(tags({Tag.동사파생접미사, Tag.동사}), form("하")).if_spaced()
    .msg("'척하다'로 붙여 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.보조사, "부터").if_spaced()
    .msg("'부터'를 앞 말에 붙여 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.동사, "차")
    .tag_form(Tag.연결어미, "고")
    .tag_form(Tag.동사, "넘치").if_not_spaced()
    .msg("'차고 넘치다'로 띄어 써야 합니다.").build(),
    
    *rule()
    .id("안 되다_1_띄어쓰기")
    .tag_form(Tag.일반명사, "얼마").context()
    .tag_form(Tag.일반부사, "안")
    .tag_form(Tag.동사, "되").if_not_spaced()
    .msg("'안 되다'로 띄어 써야 합니다.").build(),
    
    *rule()
    .id("안 되다_2_띄어쓰기")
    .AND(tags({Tag.연결어미}), forms({"어서", "으면"})).context()
    .tag(Tag.보조사).opt().context()
    .tag_form(Tag.일반부사, "안")
    .tag_form(Tag.동사, "되").if_not_spaced()
    .msg("'안 되다'로 띄어 써야 합니다.").build(),
    
    *rule()
    .id("안 되다_3_띄어쓰기")
    .tag_form(Tag.관형사, "몇").context()
    .any().opt().context()
    .tag_form(Tag.일반부사, "안")
    .tag_form(Tag.동사, "되").if_not_spaced()
    .msg("'안 되다'로 띄어 써야 합니다.").build(),

    *rule()
    .id("안 되다_4_띄어쓰기")
    .tag_form(Tag.보조사, "밖에").context()
    .tag_form(Tag.일반부사, "안")
    .tag_form(Tag.동사, "되").if_not_spaced()
    .msg("'안 되다'로 띄어 써야 합니다.").build(),

    *rule()
    .tag(Tag.관형사형전성어미)
    .tag_form(Tag.일반명사, "경우").if_not_spaced()
    .msg("'경우'를 앞 말과 띄어 써야 합니다.").build(),
]

_NNB = [
    *rule()
    .tag_form(Tag.관형사, "몇")
    .AND(tag(Tag.의존명사), forms({"번", "개", "명"})).if_not_spaced()
    .msg("'몇 {form[1]}'batchim(\"으로\",\"로\") 띄어 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.관형사, "여러")
    .AND(tag(Tag.의존명사), forms({"번", "개", "명"})).if_not_spaced()
    .msg("'여러 {form[1]}'batchim(\"으로\",\"로\") 띄어 써야 합니다.").build(),
    
    *rule()
    .id("NNB_명사_중_띄어쓰기")
    .tags({Tag.명사파생접미사, Tag.일반명사})
    .tag_form(Tag.의존명사, "중").if_not_spaced()
    .msg("'{dform[0]} 중'으로 띄어 써야 합니다.").detail("'중(中)'은 의존명사이므로 일부 합성어를 제외하고는 앞 말과 띄어 써야 합니다.\n\n합성어로 등재된 단어: 그중, 밤중, 한밤중, 은연중, 부재중, 오밤중, 무언중").build(),

    *rule()
    .AND(tag(Tag.관형사), forms(NUMBER_DETERMINERS))
    .tag(Tag.의존명사).if_not_spaced()
    .msg("'{dform[0]} {dform[1]}'batchim(\"으로\", \"로\") 띄어 써야 합니다.").build(),
    
    *rule()
    .tag(Tag.관형사)
    .tag_form(Tag.의존명사, "가지").if_not_spaced()
    .msg("'{dform[0]} 가지'로 띄어 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.관형사, "한")
    .tag_form(Tag.일반명사, "입").if_spaced()
    .NOT(tag_form(Tag.부사격조사, "으로")).context()
    .msg("'한 번 베어 무는 단위'를 나타내는 경우, '한입'으로 붙여 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.관형사, "아무")
    .tags({Tag.일반명사, Tag.의존명사, Tag.대명사}).if_not_spaced()
    .msg("'아무 {dform[1]}'batchim(\"으로\", \"로\") 띄어 써야 합니다.").build(),

    *rule()
    .tag_form(Tag.관형사, "아무")
    .AND(tag(Tag.일반명사), forms({"문제", "상관", "관계", "재미"}))
    .forms({"없", "없이"}).if_not_spaced()
    .msg("'아무 {form[1]} 없다'로 띄어 써야 합니다.").build(),

    *rule()
    .tag_form(Tag.관형사, "어느")
    .tags({Tag.의존명사, Tag.일반명사}).if_not_spaced()
    .msg("'어느 {dform[1]}'batchim(\"으로\", \"로\") 띄어 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.관형사, "어느")
    .forms({"새", "덧"}).if_spaced()
    .msg("'{form[0]}{form[1]}'batchim(\"으로\",\"로\") 붙여 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.일반부사, "더")
    .tag_form(Tag.일반명사, "이상").if_not_spaced()
    .msg("'더 이상'으로 띄어 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.의존명사, "수").context()
    .tag_form(Tag.형용사, "있").if_not_spaced()
    .msg("'있다'를 띄어 써야 합니다.").build(),
    
    *rule()
    .tag(Tag.관형사형전성어미).context()
    .tag_form(Tag.의존명사, "수").context()
    .OR(tag_form(Tag.일반부사, "없이"), tag_form(Tag.형용사, "없")).if_not_spaced()
    .msg("'없다'를 앞 말과 띄어 써야 합니다.").build(),
    
    *rule()
    .id("NNB_체언_때문_띄어쓰기")
    .tags({Tag.일반명사, Tag.고유명사, Tag.대명사, Tag.명사파생접미사})
    .tag(Tag.닫는부호).opt()
    .tag_form(Tag.의존명사, "때문").if_not_spaced()
    .msg("'때문'은 의존명사이므로, 앞 말과 띄어 써야 합니다.").build(),
    
    *rule()
    .tag(Tag.숫자)
    .tag_form(Tag.명사파생접미사, "여")
    .AND(tag(Tag.의존명사), forms({"개", "개국", "명", "곳", "초", "분", "시간", "일", "주", "개월", "년", "군데", "차례"})).if_not_spaced()
    .msg("'{dform[0]}{form[0]} {form[1]}'batchim(\"으로\",\"로\") 띄어 써야 합니다.").build(),
    
    *rule()
    .tags({Tag.일반명사, Tag.고유명사, Tag.대명사, Tag.명사파생접미사})
    .tag_form(Tag.의존명사, "간").if_not_spaced()
    .msg("'{dform[0]} 사이'의 의미인 경우, '{dform[0]} 간'으로 띄어 써야 합니다.").build(),
    
    *rule()
    .AND(tags({Tag.관형사형전성어미, Tag.관형사, Tag.관형격조사}), NOT(forms({"아무", "별", "잘"})))
    .AND(tag(Tag.의존명사), forms({"것"})).if_not_spaced()
    .msg("'것'을 앞 말과 띄어 써야 합니다.").build(),

    *rule()
    .id("것_띄어쓰기")
    .NOT(tag_form(Tag.형용사, "달")).context()
    .tags({Tag.관형사형전성어미, Tag.관형사, Tag.관형격조사})
    .AND(tag(Tag.의존명사), forms({"거"})).if_not_spaced()
    .NOT(tag_form(Tag.목적격조사, "ᆯ")).context()
    .msg("'것'을 앞 말과 띄어 써야 합니다.").build(),

    *rule()
    .id("걸_띄어쓰기")
    .AND(tag(Tag.관형사형전성어미), forms({"다는", "단", "란", "라는"})).context()
    .tag_form(Tag.의존명사, "거").if_not_spaced()
    .tag_form(Tag.목적격조사, "ᆯ")
    .msg("'것을'의 의미이므로, '걸'을 앞 말과 띄어 써야 합니다.").build(),
    
    *rule()
    .tags({Tag.관형사형전성어미, Tag.관형사, Tag.관형격조사}).context()
    .AND(tag(Tag.의존명사), forms({"채", "만큼", "바", "적", "둥", "척", "리", "뻔", "터", "줄", "대로", "김", "등", "셈"})).if_not_spaced()
    .msg("'{form[0]}'batchim(\"을\",\"를\") 앞 말과 띄어 써야 합니다.").build(),

    *rule()
    .tags({Tag.관형사형전성어미, Tag.관형사, Tag.관형격조사}).context()
    .AND(tag(Tag.일반명사), forms({"생각"}))
    .tag_form(Tag.동사파생접미사, "하").if_not_spaced()
    .msg("'{form[0]}'batchim(\"을\", \"를\") 꾸미는 말이 있으므로 '{form[0]} 하다'로 띄어 써야 합니다.").build(),

    *rule()
    .tags({Tag.관형사형전성어미})
    .AND(tag(Tag.의존명사), forms({"분"})).if_not_spaced()
    .msg("'{form[0]}'batchim(\"을\",\"를\") 앞 말과 띄어 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.관형사, "한")
    .AND(tag(Tag.의존명사), forms({"방", "푼", "닢", "아름"})).if_not_spaced()
    .msg("'한 {form[1]}'batchim(\"으로\",\"로\") 띄어 써야 합니다.").build(),

    *rule()
    .tag(Tag.관형사형전성어미).context()
    .tag_form(Tag.의존명사, "수").if_not_spaced()
    .msg("'수'를 앞 말과 띄어 써야 합니다.").build(),

    *rule()
    .tag_form(Tag.동사, "지나")
    .tag_form(Tag.관형사형전성어미, "ᆫ")
    .tag_form(Tag.의존명사, "번").if_spaced()
    .msg("'지난번'으로 붙여 써야 합니다.").build(),

    *rule()
    .NOT(tag_form(Tag.형용사규칙활용, "그렇")) # 그럴듯하다를 한 단어로 못 잡아서 추가.context()
    .tags({Tag.관형사형전성어미, Tag.관형사, Tag.관형격조사})
    .tag_form(Tag.의존명사, "듯").if_not_spaced()
    .NOT(tag_form(Tag.동사, "말")).context()
    .NOT(tag_form(Tag.의존명사, "듯")).context()
    .msg("'듯'을 앞 말과 띄어 써야 합니다.").build(),

    *rule()
    .tag(Tag.보조용언).context()
    .tag_form(Tag.관형사형전성어미, "ᆯ").context()
    .tag_form(Tag.의존명사, "만").if_not_spaced()
    .msg("'만'을 앞 말과 띄어 써야 합니다.").build(),

    *rule()
    .AND(tag(Tag.관형사형전성어미), forms({"ᆯ", "을"}))
    .tag_form(Tag.의존명사, "만").if_not_spaced()
    .tag_form(Tag.형용사파생접미사, "하").if_spaced()
    .msg("'OO할 만하다'로 띄어 써야 합니다.").build(),

    *rule()
    .id("만하다_붙여쓰기")
    .tag_form(Tag.의존명사, "만")
    .tag_form(Tag.동사, "하").if_spaced()
    .msg("'만하다'로 붙여 써야 합니다.").build(),
    
    *rule()
    .tag(Tag.일반부사) # 아무튼, 하여튼
    .tag_form(Tag.의존명사, "간").if_not_spaced()
    .msg("'{dform[0]} 간'으로 띄어 써야 합니다.").build(),

    *rule()
    .tag(Tag.일반명사)
    .tag_form(Tag.의존명사, "격").if_not_spaced()
    .msg("'{dform[0]} 격'으로 띄어 써야 합니다.").build(),

    *rule()
    .id("NNB_명사_쪽_띄어쓰기")
    .tag(Tag.일반명사)
    .tag_form(Tag.의존명사, "쪽").if_not_spaced()
    .msg("'{dform[0]} 쪽'으로 띄어 써야 합니다.").build(),

    *rule()
    .id("NNB_데다_띄어쓰기")
    .tag(Tag.관형사형전성어미).context()
    .tag_form(Tag.의존명사, "데").if_not_spaced()
    .AND(tag(Tag.보조사), forms({"다", "다가"})).context()
    .msg("'데'를 앞 말과 띄어 써야 합니다.").build(),

    *rule()
    .id("NNB_데_1_띄어쓰기")
    .form("데").if_not_spaced()
    .tag_form(Tag.부사격조사, "에").context()
    .msg("'곳'의 의미인 경우, '데'를 앞 말과 띄어 써야 합니다.").build(),

    *rule()
    .id("NNB_데_2_띄어쓰기")
    .form("데").if_not_spaced()
    .tag_form(Tag.보조사, "는").context()
    .msg("'곳'의 의미인 경우, '데'를 앞 말과 띄어 써야 합니다.").build(),

    *rule()
    .id("NNB_시_띄어쓰기")
    .tag_form(Tag.관형사형전성어미, "ᆯ").context()
    .tag_form(Tag.의존명사, "시").if_not_spaced()
    .msg("'시'를 앞 말과 띄어 써야 합니다.").build(),

    *rule()
    .id("NNB_숫자_만_띄어쓰기")
    .tag(Tag.숫자)
    .tag(Tag.의존명사)
    .tag_form(Tag.의존명사, "만").if_not_spaced()
    .msg("'{dform[0]}{dform[1]} 만'으로 띄어 써야 합니다.").build(),

    *rule()
    .id("NNB_관형사_만_띄어쓰기")
    .forms(NUMBER_DETERMINERS | {"한"})
    .tag(Tag.의존명사)
    .tag_form(Tag.의존명사, "만").if_not_spaced()
    .msg("'{dform[0]} {dform[1]} 만'으로 띄어 써야 합니다.").build(),

    *rule()
    .id("NNB_명사파생접미사 여_의존명사_띄어쓰기")
    .tag_form(Tag.명사파생접미사, "여").context()
    .tag(Tag.의존명사).if_not_spaced()
    .msg("'{dform[0]}'batchim(\"을\", \"를\") 앞 말과 띄어 써야 합니다.").build(),
]

_NNG = [
    *rule()
    .tags({Tag.일반명사, Tag.대명사, Tag.관형격조사, Tag.고유명사})
    .AND(tag(Tag.일반명사), forms({"편", "정도", "말"})).if_not_spaced()
    .msg("'{form[0]}'batchim(\"을\",\"를\") 앞 말과 띄어 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.관형사, "별")
    .AND(tag(Tag.의존명사), forms({"것", "거", "수"})).if_spaced()
    .msg("'별다른 {form[1]}'batchim(\"이라\",\"라\")는 의미의 '{form[0]}{form[1]}'batchim(\"은\",\"는\") 한 단어이므로 붙여 써야 합니다.").build(),

    *rule()
    .tag_form(Tag.관형사, "별")
    .AND(tag(Tag.일반명사), forms({"말씀", "생각", "걱정", "문제", "일"})).if_spaced()
    .msg("'별다른 {form[1]}'batchim(\"이라\",\"라\")는 의미의 '{form[0]}{form[1]}'batchim(\"은\",\"는\") 한 단어이므로 붙여 써야 합니다.").build(),

    *rule()
    .tag_form(Tag.관형사, "첫")
    .AND(tag(Tag.일반명사), forms({"해", "날"})).if_spaced()
    .msg("'첫{form[1]}'batchim(\"으로\",\"로\") 붙여 써야 합니다.").build(),

    *rule()
    .tag_form(Tag.관형사, "한")
    .AND(tag(Tag.일반명사), forms({"때", "순간"})).if_spaced()
    .msg("'한{form[1]}'batchim(\"으로\",\"로\") 붙여 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.관형사, "한")
    .AND(tag(Tag.일반명사), forms({"수", "몸"})).if_not_spaced()
    .msg("'한 {form[1]}'batchim(\"으로\",\"로\") 띄어 써야 합니다.").build(),
    
    *rule()
    .AND(tag(Tag.관형사), forms({"이", "그", "저"}))
    .AND(tag(Tag.의존명사), forms({"따위", "놈", "분"})).if_spaced()
    .msg("'{form[0]}{form[1]}'batchim(\"으로\",\"로\") 붙여 써야 합니다.").build(),
    
    *rule()
    .AND(tag(Tag.관형사), forms({"이", "그", "저"}))
    .AND(tag(Tag.의존명사), form("녀석")).if_not_spaced()
    .msg("'{form[0]} 녀석'으로 띄어 써야 합니다.").build(),
    
    *rule()
    .AND(tag(Tag.관형사), forms({"이", "그", "저"}))
    .AND(tag(Tag.일반명사), forms({"곳"})).if_spaced()
    .msg("'{form[0]}{form[1]}'으로 붙여 써야 합니다.").build(),
    
    *rule()
    .AND(tag(Tag.관형사), forms({"이", "그", "저"}))
    .AND(tag(Tag.일반명사), forms({"자식", "사람"})).if_not_spaced()
    .msg("'{form[0]} {form[1]}'으로 띄어 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.관형사, "그")
    .AND(tag(Tag.일반명사), forms({"후", "자체", "틈"})).if_not_spaced()
    .msg("'{form[0]} {form[1]}'batchim(\"으로\",\"로\") 띄어 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.관형사, "이")
    .AND(tag(Tag.일반명사), forms({"틈"})).if_not_spaced()
    .msg("'{form[0]} {form[1]}'batchim(\"으로\",\"로\") 띄어 써야 합니다.").build(),
    
    *rule()
    .id("NNB_일반명사_중_붙여쓰기")
    .AND(tag(Tag.일반명사), forms({"은연", "부재", "오밤", "무언"}))
    .tag_form(Tag.의존명사, "중").if_spaced()
    .msg("'{form[0]}중'으로 붙여 써야 합니다.").build(),

    *rule()
    .id("NNB_한밤중_붙여쓰기")
    .tag_form(Tag.체언접두사, "한")
    .tag_form(Tag.일반명사, "밤")
    .tag_form(Tag.의존명사, "중").if_spaced()
    .msg("'한밤중'으로 붙여 써야 합니다.").build(),
    
    *rule()
    .NOT(tags({Tag.일반부사, Tag.관형사형전성어미})).context()
    .tag_form(Tag.동사, "비")
    .tag_form(Tag.관형사형전성어미, "ᆫ")
    .tag_form(Tag.일반명사, "방").if_spaced()
    .msg("'빈방'으로 붙여 써야 합니다.").build(),
    
    *rule()
    .NOT(tags({Tag.관형사, Tag.관형사형전성어미})).context()
    .tag_form(Tag.동사, "비")
    .tag_form(Tag.관형사형전성어미, "ᆫ")
    .tag_form(Tag.일반명사, "자리").if_spaced()
    .msg("'빈자리'로 붙여 써야 합니다.").build(),

    *rule()
    .NOT(tags({Tag.관형사, Tag.관형사형전성어미})).context()
    .tag_form(Tag.동사, "죽")
    .tag_form(Tag.관형사형전성어미, "을")
    .tag_form(Tag.일반명사, "병").if_spaced()
    .msg("'죽을병'으로 붙여 써야 합니다.").build(),
    
    *rule()
    .NOT(tags({Tag.관형사, Tag.관형사형전성어미, Tag.형용사파생접미사, Tag.관형격조사, Tag.목적격조사})).context()
    .tag_form(Tag.형용사, "멀")
    .tag_form(Tag.관형사형전성어미, "ᆫ")
    .tag_form(Tag.일반명사, "바다").if_spaced()
    .msg("'먼바다'로 붙여 써야 합니다.").build(),

    *rule()
    .NOT(tags({Tag.관형사, Tag.관형사형전성어미, Tag.형용사파생접미사, Tag.관형격조사, Tag.목적격조사})).context()
    .tag_form(Tag.일반명사, "세상")
    .tag_form(Tag.일반명사, "일").if_spaced()
    .msg("'세상일'로 붙여 써야 합니다.").build(),

    *rule()
    .NOT(tags({Tag.관형사, Tag.관형사형전성어미, Tag.형용사파생접미사, Tag.관형격조사, Tag.목적격조사})).context()
    .tag_form(Tag.일반명사, "입")
    .tag_form(Tag.일반명사, "조심").if_spaced()
    .tag_form(Tag.동사파생접미사, "하")
    .msg("'입조심하다'로 붙여 써야 합니다.").build(),

    *rule()
    .NOT(tags({Tag.관형사, Tag.관형사형전성어미, Tag.형용사파생접미사})).context()
    .tag_form(Tag.일반명사, "군")
    .tag_form(Tag.일반명사, "자금").if_spaced()
    .msg("'군자금'으로 붙여 써야 합니다.").build(),

    *rule()
    .NOT(tags({Tag.관형사, Tag.관형사형전성어미, Tag.형용사파생접미사, Tag.관형격조사, Tag.목적격조사})).context()
    .tag_form(Tag.일반명사, "예상")
    .tag_form(Tag.의존명사, "외").if_spaced()
    .msg("'예상외'로 붙여 써야 합니다.").build(),
    
    *rule()
    .NOT(tags({Tag.관형사, Tag.관형사형전성어미, Tag.형용사파생접미사, Tag.관형격조사, Tag.목적격조사})).context()
    .tag_form(Tag.관형사, "한")
    .tag_form(Tag.일반명사, "마음").if_spaced()
    .msg("'같은 마음'의 의미일 경우 '한마음'으로 붙여 써야 합니다.").build(),
    
    *rule()
    .NOT(tags({Tag.관형사, Tag.관형사형전성어미, Tag.형용사파생접미사, Tag.관형격조사, Tag.목적격조사})).context()
    .tag_form(Tag.일반명사, "섬")
    .tag_form(Tag.일반명사, "사람").if_spaced()
    .msg("'섬사람'으로 붙여 써야 합니다.").build(),
    
    *rule()
    .id("NNG_약재료_붙여쓰기")
    .NOT(tags({Tag.관형사, Tag.관형사형전성어미, Tag.형용사파생접미사, Tag.관형격조사, Tag.목적격조사, Tag.일반명사})).context()
    .tag_form(Tag.일반명사, "약")
    .tag_form(Tag.일반명사, "재료").if_spaced()
    .msg("'약재료'로 붙여 써야 합니다.").build(),
    
    *rule()
    .NOT(tags({Tag.관형사형전성어미, Tag.형용사파생접미사, Tag.관형격조사, Tag.목적격조사})).context()
    .tag_form(Tag.일반명사, "옛날")
    .AND(tag(Tag.일반명사), forms({"얘기", "이야기"})).if_spaced()
    .msg("'옛날{form[1]}'로 붙여 써야 합니다.").build(),
    
    *rule()
    .tag(Tag.고유명사)
    .tag_form(Tag.일반명사, "경").if_not_spaced()
    .msg("작위를 나타내는 '경(卿)'은 띄어 써야 합니다.").build(),
    
    *rule()
    .tag(Tag.관형사형전성어미)
    .tag_form(Tag.일반명사, "자리").if_not_spaced()
    .msg("'자리'를 앞 말과 띄어 써야 합니다.").build(),
    
    *rule()
    .NOT(forms({"허튼"}))
    .tag_form(Tag.일반명사, "짓").if_not_spaced()
    .msg("'짓'을 앞 말과 띄어 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.관형사, "그")
    .tag_form(Tag.의존명사, "중").if_spaced()
    .msg("'그 가운데서'의 의미인 경우, '그중'으로 붙여 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.관형사, "그")
    .tag_form(Tag.일반명사, "밖").if_not_spaced()
    .tag_form(Tag.부사격조사, "에")
    .tag_form(Tag.보조사, "도")
    .msg("'그 밖'으로 띄어 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.대명사, "너")
    .tag_form(Tag.관형격조사, "의")
    .tag_form(Tag.의존명사, "놈").if_spaced()
    .msg("'네놈'으로 붙여 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.관형사, "단").context()
    .tag_form(Tag.관형사, "한")
    .tag_form(Tag.일반명사, "사람").if_not_spaced()
    .msg("'한 사람'으로 띄어 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.일반부사, "오직").context()
    .tag_form(Tag.관형사, "한")
    .tag_form(Tag.일반명사, "사람").if_not_spaced()
    .msg("'한 사람'으로 띄어 써야 합니다.").build(),
    
    *rule()
    .NOT(tag_form(Tag.일반부사, "더")).context()
    .tag_form(Tag.형용사, "달")
    .tag_form(Tag.관형사형전성어미, "ᆫ")
    .AND(tag(Tag.의존명사), forms({"것", "거"})).if_spaced()
    .msg("'단 음식'을 가리킬 때는 '단{form[2]}'batchim(\"으로\",\"로\") 붙여 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.관형사, "단")
    .tag_form(Tag.수사, "둘").if_spaced()
    .msg("'단둘'로 붙여 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.동사, "쓰")
    .tag_form(Tag.관형사형전성어미, "ᆯ")
    .tag_form(Tag.의존명사, "데").if_spaced()
    .msg("'쓸데'로 붙여 써야 합니다.").build(),

    *rule()
    .tag_form(Tag.관형사, "온")
    .tag_form(Tag.일반명사, "몸").if_spaced()
    .msg("'몸 전체'를 의미할 경우, '온몸'으로 붙여 써야 합니다.").build(),

    *rule()
    .tag_form(Tag.형용사, "크")
    .tag_form(Tag.관형사형전성어미, "ᆫ")
    .tag_form(Tag.일반명사, "돈").if_spaced()
    .msg("'큰돈'으로 붙여 써야 합니다.").build(),

    *rule()
    .tag_form(Tag.관형사, "한")
    .AND(tag(Tag.의존명사), forms({"쪽"})).if_spaced()
    .msg("'한{form[1]}'batchim(\"으로\",\"로\") 붙여 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.관형사, "한")
    .AND(tag(Tag.일반명사), forms({"몫"})).if_spaced()
    .msg("'한{form[1]}'batchim(\"으로\",\"로\") 붙여 써야 합니다.").build(),
    
    *rule()
    .AND(tag(Tag.관형사), forms({"오른", "왼"}))
    .tag_form(Tag.의존명사, "쪽").if_spaced()
    .msg("'{form[0]}쪽'으로 붙여 써야 합니다.").build(),
    
    *rule()
    .tags({Tag.일반명사, Tag.대명사, Tag.고유명사, Tag.명사파생접미사, Tag.명사형전성어미})
    .tag_form(Tag.일반명사, "덕").if_not_spaced()
    .msg("'{dform[0]} 덕'으로 띄어 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.체언접두사, "날")
    .tag_form(Tag.의존명사, "것").if_spaced()
    .msg("'날것'으로 붙여 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.형용사, "쓰")
    .tag_form(Tag.관형사형전성어미, "ᆫ")
    .tag_form(Tag.일반명사, "맛").if_spaced()
    .msg("'쓴맛'으로 붙여 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.관형사, "그")
    .tag_form(Tag.일반명사, "동안").if_spaced()
    .msg("'그동안'으로 붙여 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.동사, "내치")
    .tag_form(Tag.관형사형전성어미, "ᆫ")
    .tag_form(Tag.의존명사, "김").if_spaced()
    .msg("'내친김'으로 붙여 써야 합니다.").build(),

    *rule()
    .tag_form(Tag.관형사, "아무")
    .AND(tag(Tag.의존명사), forms({"것", "거"})).if_spaced()
    .msg("'아무{form[1]}'batchim(\"으로\",\"로\") 붙여 써야 합니다.").build(),

    *rule()
    .tag_form(Tag.일반명사, "다음")
    .tag_form(Tag.의존명사, "번").if_spaced()
    .msg("'다음번'으로 붙여 써야 합니다.").build(),

    *rule()
    .tag_form(Tag.형용사, "바르")
    .tag_form(Tag.관형사형전성어미, "ᆫ")
    .tag_form(Tag.일반명사, "말").if_spaced()
    .msg("'바른말'로 붙여 써야 합니다.").build(),

    *rule()
    .tag_form(Tag.동사, "지나")
    .tag_form(Tag.관형사형전성어미, "ᆫ")
    .tag_form(Tag.일반명사, "날").if_spaced()
    .msg("'지난날'로 붙여 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.관형사, "첫")
    .tag_form(Tag.일반명사, "걸음").if_spaced()
    .msg("'첫걸음'으로 붙여 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.일반명사, "평상")
    .tag_form(Tag.의존명사, "시").if_spaced()
    .msg("'평상시'로 붙여 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.관형사, "주")
    .tag_form(Tag.일반명사, "무대").if_spaced()
    .msg("'주무대'로 붙여 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.관형사, "허튼")
    .tag_form(Tag.일반명사, "짓").if_spaced()
    .msg("'허튼짓'으로 붙여 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.동사, "미치")
    .tag_form(Tag.관형사형전성어미, "ᆫ")
    .tag_form(Tag.의존명사, "놈").if_spaced()
    .msg("'미친놈'으로 붙여 써야 합니다.").build(),

    *rule()
    .tag_form(Tag.관형사, "새")
    .tag_form(Tag.일반명사, "출발").if_spaced()
    .msg("'새출발'로 붙여 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.어근, "깜찍")
    .tag_form(Tag.어근, "발랄").if_spaced()
    .msg("'깜찍발랄'으로 붙여 써야 합니다.").build(),
    
    *rule()
    .form("소강")
    .tag_form(Tag.일반명사, "상태").if_spaced()
    .msg("'소강상태'로 붙여 써야 합니다.").build(),
    
    *rule()
    .form("자기")
    .tag_form(Tag.일반명사, "소개").if_spaced()
    .msg("'자기소개'로 붙여 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.관형사, "그")
    .tag_form(Tag.일반명사, "때").if_spaced()
    .msg("'그때'로 붙여 써야 합니다.").build(),

    *rule()
    .tag_form(Tag.일반부사, "난생")
    .tag_form(Tag.일반명사, "처음").if_spaced()
    .msg("'난생처음'으로 붙여 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.일반명사, "주도")
    .tag_form(Tag.어근, "면밀").if_spaced()
    .msg("'주도면밀'로 붙여 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.대명사, "자기")
    .tag_form(Tag.일반명사, "희생").if_spaced()
    .msg("'자기희생'으로 붙여 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.관형사, "이")
    .tag_form(Tag.일반명사, "몸").if_not_spaced()
    .msg("'이 몸'으로 띄어 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.일반부사, "좀")
    .tag_form(Tag.일반명사, "전").if_not_spaced()
    .msg("'좀 전'으로 띄어 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.형용사, "멀")
    .tag_form(Tag.관형사형전성어미, "ᆫ")
    .tag_form(Tag.일반명사, "길").if_not_spaced()
    .msg("'먼 길'로 띄어 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.동사, "하")
    .tag_form(Tag.관형사형전성어미, "ᆯ")
    .tag_form(Tag.일반명사, "일").if_not_spaced()
    .msg("'할 일'로 띄어 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.관형사, "딴")
    .tag_form(Tag.일반명사, "길").if_not_spaced()
    .msg("'딴 길'로 띄어 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.관형사, "온")
    .tag_form(Tag.일반명사, "힘").if_not_spaced()
    .msg("'온 힘'으로 띄어 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.일반부사, "또")
    .tag_form(Tag.관형사, "다른").if_not_spaced()
    .msg("'또 다른'으로 띄어 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.일반부사, "다")
    .tag_form(Tag.일반부사, "함께").if_not_spaced()
    .msg("'다 함께'로 띄어 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.대명사, "저")
    .tag_form(Tag.관형격조사, "의")
    .tag_form(Tag.일반명사, "발").if_not_spaced()
    .msg("'자기의 발'의 의미인 경우, '제 발'로 띄어 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.관형사, "현")
    .tag_form(Tag.일반명사, "위치").if_not_spaced()
    .msg("'현 위치'로 띄어 써야 합니다.").build(),
    
    *rule()
    .tag(Tag.관형사형전성어미)
    .tag_form(Tag.일반명사, "일").if_not_spaced()
    .msg("'일'을 앞 말과 띄어 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.동사, "앓")
    .tag_form(Tag.관형사형전성어미, "는")
    .tag_form(Tag.일반명사, "소리").if_not_spaced()
    .msg("'앓는 소리'로 띄어 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.동사, "보")
    .tag_form(Tag.관형사형전성어미, "ᆫ")
    .tag_form(Tag.의존명사, "척")
    .tag_form(Tag.동사, "말")
    .tag_form(Tag.관형사형전성어미, "ᆫ")
    .tag_form(Tag.의존명사, "척") # '본척만척'은 명사로 등록되어 있으므로 이렇게 분해된다면 띄어 쓴 것.
    .msg("'본척만척'으로 붙여 써야 합니다.").build(),    
    
    *rule()
    .tag_form(Tag.동사, "보")
    .tag_form(Tag.관형사형전성어미, "ᆫ")
    .tag_form(Tag.의존명사, "체")
    .tag_form(Tag.동사, "말")
    .tag_form(Tag.관형사형전성어미, "ᆫ")
    .tag_form(Tag.의존명사, "체")# '본체만체'는 명사로 등록되어 있으므로 이렇게 분해된다면 띄어 쓴 것.
    .msg("'본체만체'로 붙여 써야 합니다.").build(),
    
    *rule()
    .tag(Tag.명사형전성어미)
    .tag_form(Tag.일반명사, "전").if_not_spaced()
    .msg("'전'을 앞 말과 띄어 써야 합니다.")
    .build(),

    *rule()
    .tag_form(Tag.형용사, "멀")
    .tag_form(Tag.관형사형전성어미, "ᆫ")
    .tag_form(Tag.일반명사, "걸음").if_not_spaced()
    .msg("'먼 걸음'으로 띄어 써야 합니다.")
    .build(),

    *rule()
    .tag_form(Tag.관형사, "별")
    .tag_form(Tag.일반명사, "볼일")
    .msg("'별 볼 일'으로 띄어 써야 합니다.").build(),
    
    *rule()
    .any()
    .tag(Tag.관형사형전성어미)
    .tag_form(Tag.일반명사, "말").if_not_spaced()
    .msg("'merge(({dform[0]}, {dtag[0]}), ({dform[1]}, {dtag[1]})) 말'로 띄어 써야 합니다.").build(),
    
    *rule()
    .id("NNG_점_띄어쓰기")
    .tag(Tag.관형사형전성어미).context()
    .tag_form(Tag.일반명사, "점").if_not_spaced()
    .msg("'점'을 앞 말과 띄어 써야 합니다.").build(),
    
    *rule()
    .id("NNG_당시_띄어쓰기")
    .tags({Tag.일반명사, Tag.고유명사})
    .tag_form(Tag.일반명사, "당시").if_not_spaced()
    .msg("'{dform[0]} 당시'로 띄어 써야 합니다.").build(),

    *rule()
    .id("NNG_동안_띄어쓰기")
    .tags({Tag.일반명사, Tag.의존명사, Tag.관형사, Tag.관형사형전성어미, Tag.명사파생접미사, Tag.명사형전성어미})
    .tag_form(Tag.일반명사, "동안").if_not_spaced()
    .msg("'{dform[0]} 동안'으로 띄어 써야 합니다.").build(),

    *rule()
    .id("NNG_관형사_자리_띄어쓰기")
    .AND(tag(Tag.관형사), forms(NUMBER_DETERMINERS - {"첫"}))
    .tag_form(Tag.일반명사, "자리").if_not_spaced()
    .msg("'{dform[0]} 자리'로 띄어 써야 합니다.").build(),

    *rule()
    .id("NNG_수사_잔_띄어쓰기")
    .tag_form(Tag.관형사, "한")
    .tag_form(Tag.일반명사, "잔").if_not_spaced()
    .tag(Tag.목적격조사).context()
    .msg("'한 잔'으로 띄어 써야 합니다.").build(),

    *rule()
    .id("NNG_OO간_붙여쓰기")
    .AND(tag(Tag.일반명사), forms({"자매", "형제", "모자", "부부", "부자", "모녀", "부녀"}))
    .tag_form(Tag.의존명사, "간").if_spaced()
    .msg("'{dform[0]}간'으로 붙여 써야 합니다.").build(),
    
    *rule()
    .id("NNG_살날_붙여쓰기")
    .tag_form(Tag.동사, "살")
    .tag_form(Tag.관형사형전성어미, "ᆯ")
    .tag_form(Tag.일반명사, "날").if_spaced()
    .msg("'앞으로 살게 될 날'의 의미인 경우, '살날'로 붙여 써야 합니다.").build(),
]

_NNG_SINGLE_WORDS = [
    *rule()
    .tags({Tag.일반명사, Tag.고유명사})
    .tag_form(Tag.일반명사, "더미").if_not_spaced()
    .msg("'{dform[0]} 더미'로 띄어 써야 합니다.").build(),

    *rule()
    .id("NNG_SINGLE_시절_띄어쓰기")
    .tag_form(Tag.일반명사, "시절").if_not_spaced()
    .msg("'시절'을 앞 말과 띄어 써야 합니다.").build(),

    *rule()
    .id("NNG_SINGLE_일정_띄어쓰기")
    .tag_form(Tag.일반명사, "일정")
    .tag(Tag.일반명사).if_not_spaced()
    .msg("'일정 {dform[1]}'batchim(\"으로\", \"로\") 띄어 써야 합니다.").build(),

    *rule()
    .id("NNG_SINGLE_뭐_띄어쓰기")
    .NOT(tags({Tag.여는부호, Tag.줄임표})).context()
    .tag_form(Tag.대명사, "뭐").if_not_spaced()
    .msg("'뭐'를 앞 말과 띄어 써야 합니다.").build(),

    *rule()
    .tags({Tag.일반명사, Tag.고유명사})
    .tag_form(Tag.일반명사, "밀착").if_not_spaced()
    .msg("'{dform[0]} 밀착'으로 띄어 써야 합니다.").build(),

    *rule()
    .tags({Tag.관형사형전성어미}).context()
    .tag_form(Tag.일반명사, "뒤").if_not_spaced()
    .msg("'뒤'를 앞 말과 띄어 써야 합니다.").build(),

    *rule()
    .tag_form(Tag.일반부사, "잠시")
    .tag_form(Tag.일반명사, "후").if_not_spaced()
    .msg("'잠시 후'로 띄어 써야 합니다.").build(),
]

_NNG_NNG = [
    *rule()
    .AND(tag(Tag.일반명사), forms({"글자", "소지"}))
    .tag_form(Tag.일반명사, "수").if_not_spaced()
    .msg("'{form[0]} 수'로 띄어 써야 합니다.").build(),
    
    *rule()
    .AND(tag(Tag.일반명사), forms({"인원", "상당", "과반", "번지"}))
    .tag_form(Tag.일반명사, "수").if_spaced()
    .msg("'{form[0]}수'로 붙여 써야 합니다.").build(),
    
    *rule()
    .AND(tag(Tag.일반명사), forms({"활용"}))
    .tag_form(Tag.일반명사, "법").if_spaced()
    .msg("'{form[0]}법'으로 붙여 써야 합니다.").build(),
    
    *rule()
    .AND(tag(Tag.일반명사), forms({"울음", "웃음", "노랫", "물"}))
    .tag_form(Tag.일반명사, "소리").if_spaced()
    .msg("'{form[0]}소리'로 붙여 써야 합니다.").build(),

    *rule()
    .AND(tag(Tag.일반명사), forms({"배신", "자살", "월권", "부정", "기만"}))
    .tag_form(Tag.일반명사, "행위").if_spaced()
    .msg("'{form[0]}행위'로 붙여 써야 합니다.").build(),

    *rule()
    .AND(tag(Tag.일반명사), forms({"여자", "남자"}))
    .AND(tag(Tag.일반명사), forms({"아이", "애"})).if_spaced()
    .msg("'{form[0]}{form[1]}'batchim(\"으로\",\"로\") 붙여 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.일반명사, "주인")
    .AND(tag(Tag.일반명사), forms({"아저씨", "아주머니", "아줌마"})).if_spaced()
    .msg("'주인{form[1]}'로 붙여 써야 합니다.").build(),
    
    *rule()
    .AND(tag(Tag.일반명사), forms({"해적", "형사"}))
    .tag_form(Tag.일반명사, "혼").if_not_spaced()
    .msg("'{form[0]} 혼'으로 띄어 써야 합니다.").build(),
    
    *rule()
    .NOT(tag(Tag.일반명사)).context()
    .tag_form(Tag.일반명사, "시간")
    .tag_form(Tag.일반명사, "제한").if_spaced()
    .msg("'시간제한'으로 붙여 써야 합니다.").build(),
    
    # 붙여 써야 하는 것
    *NNG_and_NNG("산", "속", SpacingRule.ATTACHED),
    *NNG_and_NNG("몸", "속", SpacingRule.ATTACHED),
    *NNG_and_NNG("눈", "앞", SpacingRule.ATTACHED, "'시야'의 의미인 경우 '눈앞'으로 붙여 써야 합니다. '눈(雪) 앞'인 경우는 띄어 써야 합니다."),
    *NNG_and_NNG("창", "밖", SpacingRule.ATTACHED),
    *NNG_and_NNG("문", "밖", SpacingRule.ATTACHED),
    *NNG_and_NNG("소", "머리", SpacingRule.ATTACHED),
    *NNG_and_NNG("마음", "속", SpacingRule.ATTACHED),
    *NNG_and_NNG("점심", "때", SpacingRule.ATTACHED),
    *NNG_and_NNG("단벌", "옷", SpacingRule.ATTACHED),
    *NNG_and_NNG("끝", "부분", SpacingRule.ATTACHED),
    *NNG_and_NNG("대역", "죄인", SpacingRule.ATTACHED),
    *NNG_and_NNG("유리", "구슬", SpacingRule.ATTACHED),
    *NNG_and_NNG("구급", "상자", SpacingRule.ATTACHED),
    *NNG_and_NNG("영화", "배우", SpacingRule.ATTACHED),
    *NNG_and_NNG("얼굴", "도장", SpacingRule.ATTACHED),
    *NNG_and_NNG("단골", "손님", SpacingRule.ATTACHED),
    *NNG_and_NNG("바깥", "세상", SpacingRule.ATTACHED),
    *NNG_and_NNG("결사", "반대", SpacingRule.ATTACHED),
    *NNG_and_NNG("어미", "벌레", SpacingRule.ATTACHED),
    *NNG_and_NNG("인간", "관계", SpacingRule.ATTACHED),
    *NNG_and_NNG("민간", "전승", SpacingRule.ATTACHED),
    *NNG_and_NNG("민간", "요법", SpacingRule.ATTACHED),
    *NNG_and_NNG("에덴", "동산", SpacingRule.ATTACHED),
    *NNG_and_NNG("정체", "불명", SpacingRule.ATTACHED),
    *NNG_and_NNG("황소", "고집", SpacingRule.ATTACHED),
    *NNG_and_NNG("예행", "연습", SpacingRule.ATTACHED),
    *NNG_and_NNG("기념", "사진", SpacingRule.ATTACHED),
    *NNG_and_NNG("자연", "경관", SpacingRule.ATTACHED),
    *NNG_and_NNG("자연", "재해", SpacingRule.ATTACHED),
    *NNG_and_NNG("공중", "분해", SpacingRule.ATTACHED),
    *NNG_and_NNG("선제", "공격", SpacingRule.ATTACHED),
    *NNG_and_NNG("국가", "시험", SpacingRule.ATTACHED),
    *NNG_and_NNG("고래", "수염", SpacingRule.ATTACHED),
    *NNG_and_NNG("뒷", "이야기", SpacingRule.ATTACHED),
    *NNG_and_NNG("세대", "교체", SpacingRule.ATTACHED),
    *NNG_and_NNG("밀짚", "모자", SpacingRule.ATTACHED),
    *NNG_and_NNG("갈고리", "발톱", SpacingRule.ATTACHED),
    *NNG_and_NNG("하루", "이틀", SpacingRule.ATTACHED),
    *NNG_and_NNG("말", "버릇", SpacingRule.ATTACHED),
    *NNG_and_NNG("술", "버릇", SpacingRule.ATTACHED),
    *NNG_and_NNG("정리", "정돈", SpacingRule.ATTACHED),
    *NNG_and_NNG("물결", "무늬", SpacingRule.ATTACHED),
    *NNG_and_NNG("수건", "걸이", SpacingRule.ATTACHED),
    *NNG_and_NNG("휴지", "걸이", SpacingRule.ATTACHED),
    *NNG_and_NNG("압", "속", SpacingRule.ATTACHED),
    *NNG_and_NNG("입", "안", SpacingRule.ATTACHED),
    *NNG_and_NNG("의사", "소통", SpacingRule.ATTACHED),
    
    # 띄어 써야 하는 것
    *NNG_and_NNG("수정", "구슬", SpacingRule.SPACED),
    *NNG_and_NNG("작동", "정지", SpacingRule.SPACED),
    *NNG_and_NNG("남", "일", SpacingRule.SPACED),
    *NNG_and_NNG("땅", "밑", SpacingRule.SPACED),
    *NNG_and_NNG("입", "밖", SpacingRule.SPACED),
    *NNG_and_NNG("털", "뭉치", SpacingRule.SPACED), 
    *NNG_and_NNG("인형", "옷", SpacingRule.SPACED),
    *NNG_and_NNG("인형", "탈", SpacingRule.SPACED),
    *NNG_and_NNG("뒷", "내용", SpacingRule.SPACED),
    *NNG_and_NNG("몸", "상태", SpacingRule.SPACED),
    *NNG_and_NNG("역사", "속", SpacingRule.SPACED),
    *NNG_and_NNG("얼마", "전", SpacingRule.SPACED),
    *NNG_and_NNG("공짜", "밥", SpacingRule.SPACED),
    *NNG_and_NNG("오늘", "밤", SpacingRule.SPACED),
    *NNG_and_NNG("예상", "밖", SpacingRule.SPACED),
    *NNG_and_NNG("술", "냄새", SpacingRule.SPACED),
    *NNG_and_NNG("열성", "팬", SpacingRule.SPACED),
    *NNG_and_NNG("힘", "조절", SpacingRule.SPACED),
    *NNG_and_NNG("천둥", "번개", SpacingRule.SPACED),
    *NNG_and_NNG("행동", "불능", SpacingRule.SPACED),
    *NNG_and_NNG("감사", "인사", SpacingRule.SPACED),
    *NNG_and_NNG("무단", "전재", SpacingRule.SPACED),
    *NNG_and_NNG("애로", "사항", SpacingRule.SPACED),
    *NNG_and_NNG("사건", "사고", SpacingRule.SPACED),
    *NNG_and_NNG("전체", "화면", SpacingRule.SPACED),
    *NNG_and_NNG("재기", "불능", SpacingRule.SPACED),
    *NNG_and_NNG("심신", "피폐", SpacingRule.SPACED),
    *NNG_and_NNG("장기", "자랑", SpacingRule.SPACED),
    *NNG_and_NNG("사리", "분별", SpacingRule.SPACED),
    *NNG_and_NNG("천지", "차이", SpacingRule.SPACED),
    *NNG_and_NNG("출입", "금지", SpacingRule.SPACED),
    *NNG_and_NNG("무사", "수행", SpacingRule.SPACED),
    *NNG_and_NNG("기분", "전환", SpacingRule.SPACED),
    *NNG_and_NNG("책임", "회피", SpacingRule.SPACED),
    *NNG_and_NNG("한판", "승부", SpacingRule.SPACED),
    *NNG_and_NNG("시간", "낭비", SpacingRule.SPACED),
    *NNG_and_NNG("일장", "연설", SpacingRule.SPACED),
    *NNG_and_NNG("아기", "고양이", SpacingRule.SPACED),
    *NNG_and_NNG("여자", "친구", SpacingRule.SPACED),
    *NNG_and_NNG("남자", "친구", SpacingRule.SPACED),
    *NNG_and_NNG("정신", "건강", SpacingRule.SPACED),
    *NNG_and_NNG("제조", "연도", SpacingRule.SPACED),
    *NNG_and_NNG("잠금", "해제", SpacingRule.SPACED),
    *NNG_and_NNG("자살", "사건", SpacingRule.SPACED),
    *NNG_and_NNG("타살", "사건", SpacingRule.SPACED),
    *NNG_and_NNG("비밀", "병기", SpacingRule.SPACED),
    *NNG_and_NNG("개체", "수", SpacingRule.SPACED),
    *NNG_and_NNG("중간", "부분", SpacingRule.SPACED),
]

_NR = [
    *rule()
    .tag_form(Tag.관형사, "수")
    .AND(tag(Tag.수사,), forms({"천", "십", "백", "만"})).if_spaced()
    .msg("'{form[1]}의 여러 배가 되는 수'의 의미인 경우, '{form[0]}{form[1]}'batchim(\"으로\",\"로\") 붙여 써야 합니다.").build(),

    *rule()
    .id("NR_만에 하나_띄어쓰기")
    .tag_form(Tag.수사, "만")
    .tag_form(Tag.부사격조사, "에")
    .tag_form(Tag.수사, "하나").if_not_spaced()
    .msg("'만에 하나'로 띄어 써야 합니다.").build(),
]

_VV = [
    *rule()
    .id("관형사_말_하다_띄어쓰기")
    .tags({Tag.관형격조사, Tag.관형사}).context()
    .tag_form(Tag.일반명사, "말")
    .tag_form(Tag.동사, "하").if_not_spaced()
    .msg("'말'을 꾸미는 말이 있으므로 '말 하다'로 띄어 써야 합니다.").build(),
    
    *rule()
    .id("삼다_띄어쓰기")
    .tag(Tag.일반명사)
    .tag_form(Tag.동사, "삼").if_not_spaced()
    .msg("'{dform[0]} 삼다'로 띄어 써야 합니다.").build(),
    
    *rule()
    .id("VV_명사_당하다_띄어쓰기")
    .NOT(tags({Tag.일반명사, Tag.관형격조사, Tag.관형사형전성어미})).context()
    .tag(Tag.일반명사)
    .tag_form(Tag.동사, "당하").if_spaced()
    .msg("'{dform[0]}당하다'로 붙여 써야 합니다.").build(),
    
    *rule()
    .id("VV_명사_받다_띄어쓰기")
    .AND(NOT(tags({Tag.일반명사, Tag.관형격조사, Tag.관형사형전성어미})), forms({"손길"})).context()
    .tag(Tag.일반명사)
    .tag_form(Tag.동사불규칙활용, "받").if_spaced()
    .msg("'{dform[0]}받다'로 붙여 써야 합니다.").build(),
    
    *rule()
    .id("VV_부사_하다_띄어쓰기")
    .AND(tag(Tag.일반부사), forms({"살살", "오래"}))
    .tag_form(Tag.동사, "하").if_not_spaced()
    .msg("'{form[0]} 하다'로 띄어 써야 합니다.").build(),

    *rule()
    .id("VV_의존명사_주다_띄어쓰기")
    .tag(Tag.의존명사)
    .tag_form(Tag.동사, "주").if_not_spaced()
    .msg("'주다'를 앞 말과 띄어 써야 합니다.").build(),

    *rule()
    .AND(tag(Tag.일반부사), forms({"게을리", "가까이"}))
    .tag_form(Tag.동사, "하").if_spaced()
    .msg("'{form[0]}하다'로 붙여 써야 합니다.").build(),

    *rule()
    .id("VV_잘되다_붙여쓰기")
    .AND(tag(Tag.일반부사), forms({"다", "참", "전부", "마침"})).context()
    .tag_form(Tag.일반부사, "잘")
    .AND(tags({Tag.동사, Tag.동사파생접미사}), form("되")).if_spaced()
    .msg("'잘되다'로 붙여 써야 합니다.").build(),

    *rule()
    .AND(tag(Tag.일반명사), forms({"결론", "매듭", "관련", "결정", "눈물", "결말", "종결", "죄", "줄", "짝", "특징", "한숨", "규정"}))
    .tag_form(Tag.동사규칙활용, "짓").if_spaced()
    .msg("'{form[0]}짓다'로 붙여 써야 합니다.").build(),

    *rule()
    .AND(tag(Tag.일반명사), forms({"미소", "웃음", "표정", "단정", "확정"}))
    .tag_form(Tag.동사규칙활용, "짓").if_not_spaced()
    .msg("'{form[0]} 짓다'로 띄어 써야 합니다.").build(),
    
    *rule()
    .NOT(tags({Tag.관형사, Tag.관형사형전성어미, Tag.관형격조사})).context()
    .tag_form(Tag.일반명사, "마음")
    .tag_form(Tag.동사, "먹").if_spaced()
    .msg("'마음먹다'로 붙여 써야 합니다.").build(),

    *rule()
    .NOT(tags({Tag.관형사, Tag.관형사형전성어미, Tag.관형격조사})).context()
    .tag_form(Tag.일반명사, "손")
    .tag_form(Tag.동사불규칙활용, "잡").if_spaced()
    .msg("'손잡다'로 붙여 써야 합니다.").build(),
    ## 그룹 끝

    *rule()
    .tag_form(Tag.대명사, "뭐")
    .tag_form(Tag.동사, "하").if_not_spaced()
    .any().opt().context()
    .any().opt().context()
    .tag_form(Tag.의존명사, "거").context()
    .msg("'뭐 하다'로 띄어 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.연결어미, "더니").context()
    .tag_form(Tag.대명사, "뭐")
    .tag_form(Tag.동사, "하").if_not_spaced()
    .msg("'뭐 하다'로 띄어 써야 합니다.").build(),
    
    *rule()
    .id("뭐 하다_띄어쓰기")
    .tag_form(Tag.대명사, "뭐")
    .tag_form(Tag.동사, "하").if_not_spaced()
    .msg("'무엇을 하다'의 의미인 경우, '뭐 하다'로 띄어 써야 합니다. '민망하다'의 의미인 경우에는 붙여 씁니다. (예: 빈손으로 오기 뭐해서 가져왔어요.)").build(),

    *rule()
    .tag_form(Tag.일반부사, "잘못")
    .tag_form(Tag.동사, "되").if_spaced()
    .msg("'잘못되다'로 붙여 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.동사, "달")
    .tag_form(Tag.연결어미, "라")
    .tag_form(Tag.동사, "붙").if_spaced()
    .msg("'달라붙다'로 붙여 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.동사, "들르")
    .tag_form(Tag.연결어미, "어")
    .tag_form(Tag.동사, "붙").if_spaced()
    .msg("'들러붙다'로 붙여 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.일반명사, "뒤")
    .tag_form(Tag.부사격조사, "로")
    .tag_form(Tag.동사, "하").if_spaced()
    .msg("'뒤로하다'로 붙여 써야 합니다.").build(),
        
    *rule()
    .tag(Tag.연결어미)
    .tag_form(Tag.동사, "되").if_not_spaced()
    .msg("'되다'를 띄어 써야 합니다.").build(),

    *rule()
    .id("VV_안 되다_띄어쓰기")
    .tag_form(Tag.보조사, "만").context()
    .tag_form(Tag.보조사, "은").context()
    .tag_form(Tag.일반부사, "안")
    .tag_form(Tag.동사, "되").if_not_spaced()
    .msg("'안 되다'로 띄어 써야 합니다.").build(),
    
    *rule()
    .id("VV_안 되다2_띄어쓰기")
    .tag_form(Tag.보조사, "도").context()
    .tag_form(Tag.일반부사, "안")
    .tag_form(Tag.동사, "되").if_not_spaced()
    .msg("'안 되다'로 띄어 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.일반명사, "야심")
    .tag_form(Tag.동사, "차").if_not_spaced()
    .msg("'야심 차다'로 띄어 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.동사, "뒤따르")
    .tag_form(Tag.연결어미, "어")
    .tag_form(Tag.보조용언, "오").if_spaced()
    .msg("'뒤따라오다'는 한 단어이므로 붙여 써야 합니다.").build(),
    
    *rule()
    .tag(Tag.일반명사)
    .tag_form(Tag.동사, "말").if_not_spaced()
    .msg("'말다'를 앞 말과 띄어 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.일반명사, "보잘것")
    .tag_form(Tag.형용사, "없").if_spaced()
    .msg("'보잘것없다'로 붙여 써야 합니다.").build(),

    *rule()
    .tag_form(Tag.동사, "보")
    .tag_form(Tag.관형사형전성어미, "잘")
    .tag_form(Tag.의존명사, "것").if_spaced()
    .tag_form(Tag.형용사, "없")
    .msg("'보잘것없다'로 붙여 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.동사, "보")
    .tag_form(Tag.관형사형전성어미, "잘")
    .tag_form(Tag.의존명사, "것")
    .tag_form(Tag.형용사, "없").if_spaced()
    .msg("'보잘것없다'로 붙여 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.동사, "알")
    .tag_form(Tag.연결어미, "어")
    .tag_form(Tag.보조용언, "보").if_spaced()
    .msg("'알아보다'로 붙여 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.동사불규칙활용, "잡")
    .tag_form(Tag.연결어미, "어")
    .tag_form(Tag.동사, "당기").if_spaced()
    .msg("'잡아당기다'로 붙여 써야 합니다.").build(),

    *rule()
    .tag_form(Tag.동사, "타")
    .tag_form(Tag.연결어미, "고")
    .tag_form(Tag.동사, "나").if_spaced()
    .msg("'천부적인'의 의미인 경우 '타고나다'로 붙여 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.일반부사, "어찌")
    .tag_form(Tag.동사, "되").if_not_spaced()
    .msg("'어찌 되다'로 띄어 써야 합니다.").build(),

    *rule()
    .tag_form(Tag.동사, "잃")
    .tag_form(Tag.연결어미, "어")
    .tag_form(Tag.보조용언, "버리").if_spaced()
    .msg("'잃어버리다'로 붙여 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.일반부사, "가득")
    .tag_form(Tag.동사, "차").if_not_spaced()
    .msg("'가득 차다'로 띄어 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.일반부사, "본척만척")
    .tag_form(Tag.동사, "하").if_spaced()
    .msg("'본척만척하다'로 붙여 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.일반부사, "본체만체")
    .tag_form(Tag.동사, "하").if_spaced()
    .msg("'본체만체하다'로 붙여 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.일반부사, "잘")
    .any().opt().context()
    .tag_form(Tag.일반부사, "못")
    .tag_form(Tag.동사, "하").if_spaced()
    .msg("'잘 못하다'로 붙여 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.연결어미, "ᆯ까")
    .tag_form(Tag.동사, "말")
    .tag_form(Tag.연결어미, "ᆯ까")
    .tag_form(Tag.동사, "하").if_not_spaced()
    .msg("'~까 말까 하다'로 띄어 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.연결어미, "나")
    .tag_form(Tag.동사, "말").if_not_spaced()
    .tag_form(Tag.연결어미, "나")
    .msg("'~나 마나'로 띄어 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.연결어미, "든")
    .tag_form(Tag.동사, "말").if_not_spaced()
    .tag_form(Tag.연결어미, "든")
    .msg("'~든 말든'으로 띄어 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.일반부사, "제대로")
    .tag_form(Tag.동사, "되").if_not_spaced()
    .msg("'되다'를 앞 말과 띄어 써야 합니다.").build(),

    *rule()
    .tag(Tag.대명사)
    .tag_form(Tag.동사, "오").if_not_spaced()
    .msg("'오다'를 앞 말과 띄어 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.동사, "오")
    .tag_form(Tag.연결어미, "어")
    .tag_form(Tag.동사, "닿").if_spaced()
    .msg("'와닿다'로 붙여 써아 합니다.").build(),
    
    *rule()
    .tag_form(Tag.동사, "치")
    .tag_form(Tag.연결어미, "어")
    .tag_form(Tag.보조용언, "주").if_spaced()
    .msg("'쳐주다'로 붙여 써아 합니다.").build(),
        
    *rule()
    .tag_form(Tag.보조용언, "놓")
    .tag_form(Tag.연결어미, "어")
    .tag_form(Tag.보조용언, "두").if_spaced()
    .msg("'놔두다'로 붙여 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.동사, "내")
    .tag_form(Tag.연결어미, "어")
    .tag_form(Tag.보조용언, "놓").if_spaced()
    .msg("'내놓다'로 붙여 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.동사, "참")
    .tag_form(Tag.연결어미, "다")
    .tag_form(Tag.일반부사, "못").if_spaced()
    .tag_form(Tag.동사파생접미사, "하")
    .msg("'참다못하다'로 붙여 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.동사, "듣")
    .tag_form(Tag.연결어미, "다")
    .tag_form(Tag.일반부사, "못").if_spaced()
    .tag_form(Tag.동사파생접미사, "하")
    .msg("'듣다못하다'로 붙여 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.동사, "우리")
    .tag_form(Tag.연결어미, "어")
    .tag_form(Tag.동사, "먹").if_spaced()
    .msg("'우려먹다'로 붙여 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.동사, "살")
    .tag_form(Tag.연결어미, "어")
    .tag_form(Tag.동사, "남").if_spaced()
    .msg("'살아남다'로 붙여 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.동사, "살")
    .tag_form(Tag.연결어미, "어")
    .tag_form(Tag.보조용언, "가").if_spaced()
    .msg("'살아가다'로 붙여 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.동사, "살")
    .tag_form(Tag.연결어미, "어")
    .tag_form(Tag.보조용언, "오").if_spaced()
    .msg("'살아오다'로 붙여 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.동사, "살피")
    .tag_form(Tag.연결어미, "어")
    .tag_form(Tag.보조용언, "보").if_spaced()
    .msg("'살펴보다'로 붙여 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.일반부사, "마주")
    .tag_form(Tag.동사파생접미사, "하").if_spaced()
    .msg("'마주하다'로 붙여 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.동사, "갈")
    .tag_form(Tag.연결어미, "어")
    .tag_form(Tag.동사불규칙활용, "입").if_spaced()
    .msg("'갈아입다'로 붙여 써야 합니다.").build(),

    *rule()
    .tag_form(Tag.동사, "가지")
    .tag_form(Tag.연결어미, "어")
    .tag_form(Tag.보조용언, "가").if_spaced()
    .msg("'가져가다'로 붙여 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.동사, "들")
    .tag_form(Tag.연결어미, "어")
    .tag_form(Tag.보조용언, "가").if_spaced()
    .msg("'들어가다'로 붙여 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.일반명사, "버릇")
    .tag_form(Tag.동사파생접미사, "되").if_spaced()
    .msg("'버릇되다'로 붙여 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.동사, "먹")
    .tag_form(Tag.연결어미, "고")
    .tag_form(Tag.동사, "살").if_spaced()
    .msg("'생계를 유지하다'의 의미일 경우, '먹고살다'로 붙여 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.일반명사, "밤")
    .tag_form(Tag.동사, "새").if_spaced()
    .any()
    .msg("'merge((\"밤새\", \"동사\"), ({dform[2]}, {dtag[2]}))'batchim(\"으로\", \"로\") 붙여 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.일반부사, "오래")
    .tag_form(Tag.동사, "가").if_spaced()
    .msg("'오래가다'로 붙여 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.동사, "털")
    .tag_form(Tag.연결어미, "어")
    .tag_form(Tag.보조용언, "놓").if_spaced()
    .msg("'털어놓다'로 붙여 써야 합니다.").build(),
    
    *rule()
    .NOT(tag(Tag.목적격조사)).context()
    .tag_form(Tag.동사, "누르")
    .tag_form(Tag.연결어미, "어")
    .tag_form(Tag.동사, "앉").if_spaced()
    .msg("'자리를 차지하다'의 의미인 경우 '눌러앉다'로 붙여 써야 합니다. '눌러서 앉다'인 경우는 띄어 써 주세요.").build(),
    
    *rule()
    .tag_form(Tag.동사, "내리")
    .tag_form(Tag.연결어미, "어")
    .tag_form(Tag.동사, "오").if_spaced()
    .msg("'내려오다'로 붙여 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.동사, "앞서")
    .tag_form(Tag.연결어미, "어")
    .tag_form(Tag.동사, "가").if_spaced()
    .msg("'앞서가다'로 붙여 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.동사, "물")
    .tag_form(Tag.연결어미, "어")
    .tag_form(Tag.동사불규칙활용, "뜯").if_spaced()
    .msg("'물어뜯다'로 붙여 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.동사, "따르")
    .tag_form(Tag.연결어미, "어")
    .tag_form(Tag.동사불규칙활용, "잡").if_spaced()
    .msg("'따라잡다'로 붙여 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.동사, "따르")
    .tag_form(Tag.연결어미, "어")
    .tag_form(Tag.동사, "가").if_spaced()
    .msg("'따라가다'로 붙여 써야 합니다.").build(),
    
    *rule()
    .AND(tags({Tag.감탄사, Tag.관형사}), form("저"))
    .tag_form(Tag.동사, "버리").if_spaced()
    .msg("'저버리다'로 붙여 써야 합니다.").build(),
        
    *rule()
    .tag_form(Tag.동사, "걸리")
    .tag_form(Tag.연결어미, "어")
    .tag_form(Tag.보조용언, "들").if_spaced()
    .msg("'걸려들다'로 붙여 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.동사, "알")
    .tag_form(Tag.연결어미, "어")
    .tag_form(Tag.동사규칙활용, "듣").if_spaced()
    .msg("'알아듣다'로 붙여 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.동사불규칙활용, "잡")
    .tag_form(Tag.연결어미, "어")
    .tag_form(Tag.동사, "먹").if_spaced()
    .msg("'잡아먹다'로 붙여 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.동사, "몰리")
    .tag_form(Tag.연결어미, "어")
    .tag_form(Tag.동사, "오").if_spaced()
    .msg("'몰려오다'로 붙여 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.일반부사, "가만")
    .tag_form(Tag.동사, "있").if_spaced()
    .msg("'가만있다'로 붙여 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.동사, "찾")
    .tag_form(Tag.연결어미, "어")
    .tag_form(Tag.보조용언, "내").if_spaced()
    .msg("'찾아내다'로 붙여 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.동사불규칙활용, "이르")
    .tag_form(Tag.연결어미, "어")
    .tag_form(Tag.보조용언, "두").if_spaced()
    .msg("'일러두다'로 붙여 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.동사, "돌")
    .tag_form(Tag.연결어미, "어")
    .tag_form(Tag.동사, "가").if_spaced()
    .msg("'돌아가다'로 붙여 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.형용사, "크")
    .tag_form(Tag.관형사형전성어미, "ᆫ")
    .tag_form(Tag.일반명사, "코")
    .tag_form(Tag.동사, "다치").if_spaced()
    .msg("'큰코다치다'로 붙여 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.동사, "녹")
    .tag_form(Tag.연결어미, "어")
    .tag_form(Tag.동사, "내리").if_spaced()
    .msg("'녹아내리다'로 붙여 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.동사, "찢")
    .tag_form(Tag.연결어미, "어")
    .tag_form(Tag.동사, "발기").if_spaced()
    .msg("'찢어발기다'로 붙여 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.동사, "빠지")
    .tag_form(Tag.연결어미, "어")
    .tag_form(Tag.보조용언, "나가").if_spaced()
    .msg("'빠져나가다'로 붙여 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.동사, "넘치")
    .tag_form(Tag.연결어미, "어")
    .tag_form(Tag.동사, "흐르").if_spaced()
    .msg("'넘쳐흐르다'로 붙여 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.동사, "기")
    .tag_form(Tag.연결어미, "어")
    .tag_form(Tag.동사, "다니").if_spaced()
    .msg("'기어다니다'로 붙여 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.동사, "눈여기")
    .tag_form(Tag.연결어미, "어")
    .tag_form(Tag.동사, "보").if_spaced()
    .msg("'눈여겨보다'로 붙여 써야 합니다.").build(),
        
    *rule()
    .tag_form(Tag.동사, "들이")
    .tag_form(Tag.연결어미, "어")
    .tag_form(Tag.동사, "보내").if_spaced()
    .msg("'들여보내다'로 붙여 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.일반명사, "몸")
    .tag_form(Tag.일반명사, "조심")
    .tag_form(Tag.동사파생접미사, "하")
    .msg("'몸조심하다'로 붙여 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.동사, "부둥키")
    .tag_form(Tag.연결어미, "어")
    .tag_form(Tag.동사, "안").if_spaced()
    .msg("'부둥켜안다'로 붙여 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.동사불규칙활용, "받")
    .tag_form(Tag.연결어미, "어")
    .tag_form(Tag.동사, "넘기").if_spaced()
    .msg("'받아넘기다'로 붙여 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.동사, "울")
    .tag_form(Tag.연결어미, "고")
    .tag_form(Tag.동사, "불")
    .tag_form(Tag.연결어미, "고")
    .tag_form(Tag.동사, "하")
    .msg("'울고불고하다'로 붙여 써야 합니다.").build(),

    *rule()
    .tag_form(Tag.동사, "잊")
    .tag_form(Tag.연결어미, "어")
    .tag_form(Tag.보조용언, "버리").if_spaced()
    .msg("'잊어버리다'로 붙여 써야 합니다.").build(),

    *rule()
    .tag_form(Tag.동사, "찾")
    .tag_form(Tag.연결어미, "어")
    .tag_form(Tag.동사, "다니").if_spaced()
    .msg("'찾아다니다'로 붙여 써야 합니다.").build(),

    *rule()
    .tag_form(Tag.일반부사, "한바탕")
    .tag_form(Tag.동사, "하").if_spaced()
    .msg("'한바탕하다'로 붙여 써야 합니다.").build(),

    *rule()
    .tag_form(Tag.동사, "들이")
    .tag_form(Tag.연결어미, "어다")
    .tag_form(Tag.동사, "보").if_spaced()
    .msg("'들여다보다'로 붙여 써야 합니다.").build(),

    *rule()
    .tag_form(Tag.동사규칙활용, "닫")
    .tag_form(Tag.연결어미, "어")
    .tag_form(Tag.동사, "오르").if_spaced()
    .msg("'달아오르다'로 붙여 써야 합니다.").build(),

    *rule()
    .tag_form(Tag.일반부사, "가로")
    .AND(tag(Tag.동사), forms({"막히", "막"})).if_spaced()
    .msg("'가로막다'로 붙여 써야 합니다.").build(),

    *rule()
    .tag_form(Tag.동사, "틀")
    .tag_form(Tag.연결어미, "어")
    .tag_form(Tag.동사, "막").if_spaced()
    .msg("'틀어막다'로 붙여 써야 합니다.").build(),

    *rule()
    .tag_form(Tag.의존명사, "셈")
    .tag_form(Tag.동사, "치").if_not_spaced()
    .msg("'셈 치다'로 띄어 써야 합니다.").build(),

    *rule()
    .tag_form(Tag.일반부사, "마주")
    .tag_form(Tag.동사, "보").if_not_spaced()
    .msg("'마주 보다'로 띄어 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.수사, "둘째")
    .tag_form(Tag.동사, "치").if_not_spaced()
    .msg("'둘째 치다'로 띄어 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.일반부사, "못다")
    .tag_form(Tag.동사, "하").if_not_spaced()
    .msg("'못다 하다'로 띄어 써야 합니다.").build(),

    *rule()
    .tag_form(Tag.일반부사, "이쯤")
    .tag_form(Tag.동사, "하").if_not_spaced()
    .msg("'이쯤 하다'로 띄어 써야 합니다.").build(),

    *rule()
    .tag_form(Tag.대명사, "그")
    .tag_form(Tag.명사파생접미사, "쯤")
    .tag_form(Tag.동사, "하").if_not_spaced()
    .msg("'그쯤하다'로 붙여 써야 합니다.").build(),

    *rule()
    .tag_form(Tag.동사, "헤어나오")
    .msg("'헤어 나오다'로 띄어 쓰거나, '헤어나다'로 써야 합니다.").build(),

    *rule()
    .tag_form(Tag.동사, "내버리")
    .tag_form(Tag.연결어미, "어")
    .tag_form(Tag.보조용언, "두").if_spaced()
    .msg("'내버려두다'로 붙여 써야 합니다.").build(),

    *rule()
    .tag_form(Tag.대명사, "나")
    .tag_form(Tag.동사, "모르").if_not_spaced()
    .tag_form(Tag.연결어미, "어라")
    .msg("'나 몰라라'로 띄어 써야 합니다.").build(),

    *rule()
    .tag_form(Tag.동사, "가지")
    .tag_form(Tag.연결어미, "어다")
    .tag_form(Tag.보조용언, "달").if_not_spaced()
    .any()
    .msg("'가져다 merge((\"달\", \"보조용언\"), ({dform[3]}, {dtag[3]}))'batchim(\"으로\", \"로\") 띄어 써야 합니다.").build(),   

    *rule()
    .tag_form(Tag.동사, "데리")
    .tag_form(Tag.연결어미, "어다")
    .tag_form(Tag.보조용언, "달").if_not_spaced()
    .any()
    .msg("'데려다 merge((\"달\", \"보조용언\"), ({dform[3]}, {dtag[3]}))'batchim(\"으로\", \"로\") 띄어 써야 합니다.").build(),

    *rule()
    .tag_form(Tag.일반부사, "헛되이")
    .tag_form(Tag.동사, "하").if_not_spaced()
    .msg("'헛되이 하다'로 띄어 써야 합니다.").build(),

    *rule()
    .any()
    .tag_form(Tag.연결어미, "어")
    .tag_form(Tag.동사, "보이").if_not_spaced()
    .msg("'merge(({dform[0]}, {dtag[0]}), (\"어\", \"연결어미\")) 보이다'로 띄어 써야 합니다.").build(),

    *rule()
    .tag_form(Tag.동사, "돌")
    .tag_form(Tag.연결어미, "어")
    .tag_form(Tag.동사, "다니").if_spaced()
    .msg("'돌아다니다'로 붙여 써야 합니다.").build(),
    
    # merge 결과가 이상해서 분리
    *rule()
    .tag_form(Tag.동사, "베")
    .tag_form(Tag.연결어미, "어")
    .tag_form(Tag.동사, "넘기").if_not_spaced()
    .msg("'베어 넘기다'로 띄어 써야 합니다.").build(),

    *rule()
    .tag_form(Tag.일반부사, "이래라저래라")
    .tag_form(Tag.동사, "하").if_not_spaced()
    .msg("'이래라저래라 하다'로 띄어 써야 합니다.").build(),
    
    *rule()
    .id("적당히_하다_띄어쓰기")
    .tag_form(Tag.일반부사, "적당히")
    .tag_form(Tag.동사, "하").if_not_spaced()
    .msg("'적당히 하다'로 띄어 써야 합니다.").build(),
    
    *rule()
    .id("계속하다_붙여쓰기")
    .tag_form(Tag.일반부사, "계속")
    .tag_form(Tag.동사, "하").if_spaced()
    .msg("'계속하다'로 붙여 써야 합니다.").build(),
    
    *rule()
    .tag(Tag.일반명사)
    .tag_form(Tag.동사, "부리").if_not_spaced()
    .msg("'{dform[0]} 부리다'로 띄어 써야 합니다.").build(),
    
    *rule()
    .id("사그라들다_붙여쓰기")
    .tag_form(Tag.동사, "사")
    .tag_form(Tag.연결어미, "어")
    .tag_form(Tag.동사, "그라")
    .tag_form(Tag.연결어미, "어")
    .tag_form(Tag.보조용언, "들").if_spaced()
    .msg("'사그라들다'로 붙여 써야 합니다.").build(),
    
    *rule()
    .id("VV_우러나오다_붙여쓰기")
    .tag_form(Tag.어근, "우러")
    .tag_form(Tag.동사, "나오").if_spaced()
    .msg("'우러나오다'로 붙여 써야 합니다.").build(),
    
    *rule()
    .id("VV_나타내다_붙여쓰기")
    .tag_form(Tag.어근, "나타")
    .tag_form(Tag.동사, "내").if_spaced()
    .msg("'나타내다'로 붙여 써야 합니다.").build(),
    
    *rule()
    .id("VV_그만하다_붙여쓰기")
    .tag_form(Tag.일반부사, "그만")
    .tag_form(Tag.동사, "하").if_spaced()
    .msg("'그만하다'로 붙여 써야 합니다.").build(),
    
    *rule()
    .id("VV_똑 부러지다_띄어쓰기")
    .tag_form(Tag.일반부사, "똑")
    .tag_form(Tag.동사, "부러지").if_not_spaced()
    .msg("'똑 부러지다'로 띄어 써야 합니다.").build(),
    
    *rule()
    .id("VV_위해_띄어쓰기")
    .tag_form(Tag.동사, "위하").if_not_spaced()
    .msg("'위하다'를 앞 말과 띄어 써야 합니다.").build(),
    
    *rule()
    .id("VV_쩔쩔매다_붙여쓰기")
    .form("쩔쩔")
    .tag_form(Tag.동사, "매").if_spaced()
    .msg("'쩔쩔매다'로 붙여 써야 합니다.").build(),

    *rule()
    .NOT(form("손")).context()
    .tag_form(Tag.동사, "들")
    .tag_form(Tag.연결어미, "고")
    .tag_form(Tag.동사, "나오").if_spaced()
    .msg("'들고나오다'로 붙여 써야 합니다.").build(),
]

_NNG_VV = [
    # 붙여 써야 하는 것
    *NNG_and_some("열", "받", "동사불규칙활용", SpacingRule.ATTACHED),
    *NNG_and_some("맛", "보", "동사", SpacingRule.ATTACHED),
    *NNG_and_some("손", "쓰", "동사", SpacingRule.ATTACHED),
    *NNG_and_some("기", "죽", "동사", SpacingRule.ATTACHED),
    *NNG_and_some("겁", "먹", "동사", SpacingRule.ATTACHED),
    *NNG_and_some("화", "내", "동사", SpacingRule.ATTACHED),
    *NNG_and_some("힘", "쓰", "동사", SpacingRule.ATTACHED),
    *NNG_and_some("수", "놓", "동사", SpacingRule.ATTACHED),
    *NNG_and_some("수", "놓이", "동사", SpacingRule.ATTACHED),
    *NNG_and_some("한눈", "팔", "동사", SpacingRule.ATTACHED),
    *NNG_and_some("소리", "치", "동사", SpacingRule.ATTACHED),
    *NNG_and_some("눈치", "채", "동사", SpacingRule.ATTACHED),
    *NNG_and_some("남", "모르", "동사", SpacingRule.ATTACHED),
    *NNG_and_some("한잔", "하", "동사", SpacingRule.ATTACHED),
    *NNG_and_some("앞장", "서", "동사", SpacingRule.ATTACHED),
    *NNG_and_some("내기", "하", "동사", SpacingRule.ATTACHED),
    *NNG_and_some("큰소리", "치", "동사", SpacingRule.ATTACHED),
    *NNG_and_some("혼쭐", "내", "동사", SpacingRule.ATTACHED),
    *NNG_and_some("내동댕이", "치", "동사", SpacingRule.ATTACHED),
    *NNG_and_some("결판", "내", "동사", SpacingRule.ATTACHED),
    *NNG_and_some("생색", "내", "동사", SpacingRule.ATTACHED),
    *NNG_and_some("성질", "내", "동사", SpacingRule.ATTACHED),
    *NNG_and_some("혼쭐", "나", "동사", SpacingRule.ATTACHED),
    *NNG_and_some("한턱", "내", "동사", SpacingRule.ATTACHED),
    *NNG_and_some("소문", "내", "동사", SpacingRule.ATTACHED),
    *NNG_and_some("소문", "나", "동사", SpacingRule.ATTACHED),
    *NNG_and_some("작살", "나", "동사", SpacingRule.ATTACHED),
    *NNG_and_some("끝장", "내", "동사", SpacingRule.ATTACHED),
    *NNG_and_some("조각", "내", "동사", SpacingRule.ATTACHED),
    *NNG_and_some("조각", "나", "동사", SpacingRule.ATTACHED),
    *NNG_and_some("기승", "부리", "동사", SpacingRule.ATTACHED),
    *NNG_and_some("꺼드럭", "대", "동사", SpacingRule.ATTACHED),
    *NNG_and_some("꺼드럭", "거리", "동사", SpacingRule.ATTACHED),
    *NNG_and_some("본", "받", "동사", SpacingRule.ATTACHED),

    # 띄어 써야 하는 것
    *NNG_and_some("물", "흐르", "동사", SpacingRule.SPACED),
    *NNG_and_some("눈독", "들이", "동사", SpacingRule.SPACED),
    *NNG_and_some("큰일", "나", "동사", SpacingRule.SPACED),
    *NNG_and_some("야심", "차", "동사", SpacingRule.SPACED),
    *NNG_and_some("보초", "서", "동사", SpacingRule.SPACED),
    *NNG_and_some("활개", "치", "동사", SpacingRule.SPACED),
    *NNG_and_some("눈물", "나", "동사", SpacingRule.SPACED),
    *NNG_and_some("걸음", "하", "동사", SpacingRule.SPACED),
    *NNG_and_some("나이", "들", "동사", SpacingRule.SPACED),
    *NNG_and_some("숨", "쉬", "동사", SpacingRule.SPACED),
    *NNG_and_some("숨", "막히", "동사", SpacingRule.SPACED),
    *NNG_and_some("밥", "먹", "동사", SpacingRule.SPACED),
    *NNG_and_some("초", "치", "동사", SpacingRule.SPACED),
    *NNG_and_some("짜증", "나", "동사", SpacingRule.SPACED),
    *NNG_and_some("트집", "잡히", "동사", SpacingRule.SPACED),
    *NNG_and_some("트집", "잡", "동사불규칙활용", SpacingRule.SPACED),
    *NNG_and_some("멋", "부리", "동사", SpacingRule.SPACED),
    *NNG_and_some("박살", "나", "동사", SpacingRule.SPACED),
    *NNG_and_some("사고", "치", "동사", SpacingRule.SPACED),
    *NNG_and_some("고장", "나", "동사", SpacingRule.SPACED),
    *NNG_and_some("신경", "쓰", "동사", SpacingRule.SPACED),
    *NNG_and_some("자리", "잡", "동사불규칙활용", SpacingRule.SPACED),
    *NNG_and_some("짐작", "가", "동사", SpacingRule.SPACED),
    *NNG_and_some("수다", "떨", "동사", SpacingRule.SPACED),
    *NNG_and_some("입", "다물", "동사", SpacingRule.SPACED),
    *NNG_and_some("흉내", "내", "동사", SpacingRule.SPACED),
    *NNG_and_some("전세", "내", "동사", SpacingRule.SPACED),
    *NNG_and_some("시비", "걸", "동사", SpacingRule.SPACED),
    *NNG_and_some("상처", "입", "동사불규칙활용", SpacingRule.SPACED),
    *NNG_and_some("소리", "나", "동사", SpacingRule.SPACED),
    *NNG_and_some("소리", "내", "동사", SpacingRule.SPACED),
    *NNG_and_some("손해", "보", "동사", SpacingRule.SPACED),
    *NNG_and_some("무릎", "꿇", "동사", SpacingRule.SPACED),
    *NNG_and_some("발버둥", "치", "동사", SpacingRule.SPACED),
    *NNG_and_some("사치", "부리", "동사", SpacingRule.SPACED),
    *NNG_and_some("정신", "차리", "동사", SpacingRule.SPACED),
    *NNG_and_some("판가름", "나", "동사", SpacingRule.SPACED),
    *NNG_and_some("소름", "돋", "동사불규칙활용", SpacingRule.SPACED),
    *NNG_and_some("이득", "보", "동사", SpacingRule.SPACED),
    *NNG_and_some("뒷짐", "지", "동사", SpacingRule.SPACED),
    *NNG_and_some("약", "올리", "동사", SpacingRule.SPACED),
    *NNG_and_some("주눅", "들", "동사", SpacingRule.SPACED),
    *NNG_and_some("가슴", "뛰", "동사", SpacingRule.SPACED),
]

_VV_EC_VV = [
    # 붙여 써야 하는 것
    *VV_EC_VV(("돕", "동사규칙활용"), "어", ("주", "보조용언"), SpacingRule.ATTACHED),
    *VV_EC_VV(("돕", "동사규칙활용"), "어", ("드리", "보조용언"), SpacingRule.ATTACHED),
    *VV_EC_VV(("열", "동사"), "어", ("젖히", "동사"), SpacingRule.ATTACHED),
    *VV_EC_VV(("묻", "동사규칙활용"), "어", ("보", "보조용언"), SpacingRule.ATTACHED),
    *VV_EC_VV(("찾", "동사"), "어", ("보", "보조용언"), SpacingRule.ATTACHED),
    *VV_EC_VV(("들", "동사"), "어", ("오", "동사"), SpacingRule.ATTACHED),
    *VV_EC_VV(("돌", "동사"), "어", ("오", "동사"), SpacingRule.ATTACHED),
    *VV_EC_VV(("가지", "동사"), "어", ("오", "동사"), SpacingRule.ATTACHED),
    *VV_EC_VV(("다니", "동사"), "어", ("오", "동사"), SpacingRule.ATTACHED),
    *VV_EC_VV(("따르", "동사"), "어", ("오", "동사"), SpacingRule.ATTACHED),
    *VV_EC_VV(("데리", "동사"), "어", ("오", "동사"), SpacingRule.ATTACHED),
    *VV_EC_VV(("달리", "동사"), "어", ("오", "동사"), SpacingRule.ATTACHED),
    *VV_EC_VV(("날", "동사"), "어", ("오", "동사"), SpacingRule.ATTACHED),
    *VV_EC_VV(("뛰", "동사"), "어", ("오", "동사"), SpacingRule.ATTACHED),
    *VV_EC_VV(("들리", "동사"), "어", ("오", "보조용언"), SpacingRule.ATTACHED),
    *VV_EC_VV(("건너", "동사"), "어", ("오", "보조용언"), SpacingRule.ATTACHED),
    *VV_EC_VV(("다그", "동사"), "어", ("오", "보조용언"), SpacingRule.ATTACHED),
    *VV_EC_VV(("부르", "동사"), "어", ("오", "보조용언"), SpacingRule.ATTACHED),
    *VV_EC_VV(("몰리", "동사"), "어", ("오", "보조용언"), SpacingRule.ATTACHED),
    *VV_EC_VV(("찾", "동사"), "어", ("오", "보조용언"), SpacingRule.ATTACHED),
    *VV_EC_VV(("쫓", "동사"), "어", ("오", "동사"), SpacingRule.ATTACHED),
    *VV_EC_VV(("밝히", "동사"), "어", ("내", "보조용언"), SpacingRule.ATTACHED),
    *VV_EC_VV(("알", "동사"), "어", ("내", "보조용언"), SpacingRule.ATTACHED),
    *VV_EC_VV(("끌", "동사"), "어", ("내", "보조용언"), SpacingRule.ATTACHED),
    *VV_EC_VV(("뽑", "동사불규칙활용"), "어", ("내", "보조용언"), SpacingRule.ATTACHED),
    *VV_EC_VV(("풀", "동사"), "어", ("내", "보조용언"), SpacingRule.ATTACHED),
    *VV_EC_VV(("뽑", "동사"), "어", ("내", "보조용언"), SpacingRule.ATTACHED),
    *VV_EC_VV(("담", "동사"), "어", ("내", "보조용언"), SpacingRule.ATTACHED),
    *VV_EC_VV(("가리", "동사"), "어", ("내", "보조용언"), SpacingRule.ATTACHED),
    *VV_EC_VV(("도리", "동사"), "어", ("내", "보조용언"), SpacingRule.ATTACHED),
    *VV_EC_VV(("바르", "동사"), "어", ("내", "보조용언"), SpacingRule.ATTACHED),
    *VV_EC_VV(("고르", "동사"), "어", ("내", "보조용언"), SpacingRule.ATTACHED),
    *VV_EC_VV(("꾀", "동사"), "어", ("내", "보조용언"), SpacingRule.ATTACHED),
    *VV_EC_VV(("밀", "동사"), "어", ("내", "보조용언"), SpacingRule.ATTACHED),
    *VV_EC_VV(("몰", "동사"), "어", ("내", "보조용언"), SpacingRule.ATTACHED),
    *VV_EC_VV(("짓", "동사규칙활용"), "어", ("내", "보조용언"), SpacingRule.ATTACHED),
    *VV_EC_VV(("뿜", "동사"), "어", ("내", "보조용언"), SpacingRule.ATTACHED),
    *VV_EC_VV(("가르", "동사"), "어", ("내", "보조용언"), SpacingRule.ATTACHED),
    *VV_EC_VV(("쫓", "동사"), "어", ("내", "보조용언"), SpacingRule.ATTACHED),
    *VV_EC_VV(("부르", "동사"), "어", ("내", "보조용언"), SpacingRule.ATTACHED),
    *VV_EC_VV(("건네", "동사"), "어", ("주", "보조용언"), SpacingRule.ATTACHED),
    *VV_EC_VV(("모르", "동사"), "어", ("주", "보조용언"), SpacingRule.ATTACHED),
    *VV_EC_VV(("알", "동사"), "어", ("주", "보조용언"), SpacingRule.ATTACHED),
    *VV_EC_VV(("흐르", "동사"), "어", ("나오", "동사"), SpacingRule.ATTACHED),
    *VV_EC_VV(("튀", "동사"), "어", ("나오", "동사"), SpacingRule.ATTACHED),
    *VV_EC_VV(("뛰", "동사"), "어", ("나오", "동사"), SpacingRule.ATTACHED),
    *VV_EC_VV(("뛰치", "동사"), "어", ("나오", "동사"), SpacingRule.ATTACHED),
    *VV_EC_VV(("빠지", "동사"), "어", ("나오", "동사"), SpacingRule.ATTACHED),
    *VV_EC_VV(("삐지", "동사"), "어", ("나오", "동사"), SpacingRule.ATTACHED),
    *VV_EC_VV(("풀리", "동사"), "어", ("나오", "동사"), SpacingRule.ATTACHED),
    *VV_EC_VV(("갈", "동사"), "고", ("닦", "동사"), SpacingRule.ATTACHED),
    *VV_EC_VV(("싸", "동사"), "고", ("돌", "동사"), SpacingRule.ATTACHED),
    *VV_EC_VV(("돌리", "동사"), "어", ("주", "보조용언"), SpacingRule.ATTACHED),
    *VV_EC_VV(("돌리", "동사"), "어", ("드리", "보조용언"), SpacingRule.ATTACHED),
    *VV_EC_VV(("지키", "동사"), "어", ("보", "보조용언"), SpacingRule.ATTACHED, None, "'주의깊게 보다'의 의미인 경우 붙여 써야 합니다. '보호해 보다'의 의미인 경우 띄어 써도, 붙여 써도 됩니다."),
    *VV_EC_VV(("뜨", "동사"), "어", ("내려오", "동사"), SpacingRule.ATTACHED),
    *VV_EC_VV(("흐르", "동사"), "어", ("넘치", "동사"), SpacingRule.ATTACHED),
    *VV_EC_VV(("쫓", "동사"), "어", ("다니", "동사"), SpacingRule.ATTACHED),
    *VV_EC_VV(("구르", "동사"), "어", ("다니", "동사"), SpacingRule.ATTACHED),
    *VV_EC_VV(("얻", "동사불규칙활용"), "어", ("맞", "동사"), SpacingRule.ATTACHED),
    
    # 띄어 써야 하는 것
    *VV_EC_VV(("밀", "동사"), "어", ("넣", "동사"), SpacingRule.SPACED),
    *VV_EC_VV(("쌓", "동사"), "어", ("올리", "동사"), SpacingRule.SPACED),
    *VV_EC_VV(("놀", "동사"), "러", ("오", "동사"), SpacingRule.SPACED),
    *VV_EC_VV(("놀", "동사"), "러", ("가", "동사"), SpacingRule.SPACED),
    *VV_EC_VV(("꺼내", "동사"), "어", ("들", "동사"), SpacingRule.SPACED),
    *VV_EC_VV(("따르", "동사"), "어", ("하", "동사"), SpacingRule.SPACED),
    *VV_EC_VV(("부리", "동사"), "어", ("먹", "보조용언"), SpacingRule.SPACED),
    *VV_EC_VV(("줍", "동사규칙활용"), "어", ("담", "동사"), SpacingRule.SPACED),
    *VV_EC_VV(("꽂", "동사"), "어", ("넣", "동사"), SpacingRule.SPACED),
    *VV_EC_VV(("헤치", "동사"), "어", ("나가", "보조용언"), SpacingRule.SPACED),
    *VV_EC_VV(("헤치", "동사"), "어", ("나오", "동사"), SpacingRule.SPACED),
    *VV_EC_VV(("갖", "동사"), "다", ("붙이", "동사"), SpacingRule.SPACED),
    *VV_EC_VV(("맞서", "동사"), "어", ("싸우", "동사"), SpacingRule.SPACED),
    *VV_EC_VV(("속", "동사"), "어", ("넘어가", "동사"), SpacingRule.SPACED),
    *VV_EC_VV(("먹", "동사"), "어", ("치우", "보조용언"), SpacingRule.SPACED),
    *VV_EC_VV(("돌이키", "동사"), "어", ("보", "보조용언"), SpacingRule.SPACED),
    *VV_EC_VV(("솟구치", "동사"), "어", ("나오", "동사"), SpacingRule.SPACED),
    *VV_EC_VV(("높이", "동사"), "어", ("부르", "동사"), SpacingRule.SPACED),
    *VV_EC_VV(("갈", "동사"), "어", ("넣", "동사"), SpacingRule.SPACED),
]

_VX = [
    *rule()
    .tag_form(Tag.연결어미, "고").context()
    .tag_form(Tag.보조용언, "싶").context()
    .tag_form(Tag.연결어미, "어")
    .tag_form(Tag.보조용언, "하").if_not_spaced()
    .msg("'~고 싶어 하다'로 띄어 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.명사형전성어미, "기")
    .AND(tag(Tag.보조사), forms({"ᆫ", "는"}))
    .tag_form(Tag.보조용언, "하").if_not_spaced()
    .msg("'~merge(({dform[0]}, {dtag[0]}), ({dform[1]}, {dtag[1]})) 하다'로 띄어 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.연결어미, "게").context()
    .tag_form(Tag.보조용언, "하")
    .tag_form(Tag.연결어미, "어")
    .tag_form(Tag.보조용언, "주").if_not_spaced()
    .msg("'~게 해 주다'로 띄어 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.연결어미, "어야")
    .tag_form(Tag.보조용언, "하").if_not_spaced()
    .msg("'~야 하다'로 띄어 써야 합니다.").build(),
    
    *rule()
    .tag(Tag.동사)
    .tag_form(Tag.연결어미, "어")
    .tag_form(Tag.보조용언, "하").if_not_spaced()
    .msg("'merge(({dform[0]}, {dtag[0]}), (\"어\", \"연결어미\")) 하다'로 띄어 써야 합니다.").build(),
    
    *rule()
    .tag(Tag.연결어미)
    .tag_form(Tag.보조용언, "않").if_not_spaced()
    .AND(tag(Tag.관형사형전성어미), forms({"는", "은"})).context()
    .msg("'않다'를 앞 말과 띄어 써야 합니다.").build(),
    
    *rule()
    .tags({Tag.일반명사, Tag.연결어미})
    .tag_form(Tag.보조용언, "말").if_not_spaced()
    .msg("'말다(마)'를 앞 말과 띄어 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.연결어미, "지")
    .tag(Tag.보조사).opt()
    .tag_form(Tag.보조용언, "말")
    .tag_form(Tag.연결어미, "어")
    .tag_form(Tag.보조용언, "주").if_not_spaced()
    .msg("'~지 말아 줘'와 같이, '주다'를 앞 말과 띄어 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.연결어미, "나")
    .tag_form(Tag.보조용언, "보").if_not_spaced()
    .msg("'~나 보다'로 띄어 써야 합니다.").build(),
    
    *rule()
    .AND(tag(Tag.연결어미), forms({"ᆫ가", "은가"}))
    .tag_form(Tag.보조용언, "보").if_not_spaced()
    .msg("'~가 보다'로 띄어 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.연결어미, "다")
    .tag_form(Tag.보조용언, "보").if_not_spaced()
    .AND(tag(Tag.연결어미), forms({"면", "니까", "니"}))
    .msg("'~다 보{form[2]}'batchim(\"으로\",\"로\") 띄어 써야 합니다.")
    .build(),
    
    *rule()
    .any()
    .tag_form(Tag.연결어미, "어")
    .tag_form(Tag.보조용언, "지")
    .tag_form(Tag.연결어미, "어")
    .tag_form(Tag.보조용언, "있").if_not_spaced()
    .msg("'merge(({dform[0]}, {dtag[0]}), (\"어\", \"연결어미\"))져 있다'로 띄어 써야 합니다.").build(),

    *rule()
    .tag_form(Tag.연결어미, "지")
    .tag_form(Tag.보조용언, "못하").if_not_spaced()
    .msg("'~지 못하다'로 띄어 써야 합니다.").build(),

    *rule()
    .tag_form(Tag.연결어미, "다")
    .tag_form(Tag.일반부사, "못").if_not_spaced()
    .tag_form(Tag.동사파생접미사, "하").context()
    .msg("'~다 못하다'로 띄어 써야 합니다.").build(),
    
    *rule()
    .id("못 해 먹다_띄어쓰기")
    .tag_form(Tag.일반부사, "못")
    .tag_form(Tag.동사, "하")
    .tag_form(Tag.연결어미, "어")
    .tag_form(Tag.보조용언, "먹").if_not_spaced()
    .msg("'못 해 먹겠다'로 띄어 써야 합니다.").build(),
    
    *rule()
    .id("ㄹ까 봐_띄어쓰기")
    .tag_form(Tag.연결어미, "ᆯ까")
    .tag_form(Tag.보조용언, "보").if_not_spaced()
    .msg("'~까 봐'로 띄어 써야 합니다.").build(),
    
    *rule()
    .id("게 하다_띄어쓰기")
    .tag_form(Tag.연결어미, "게")
    .tag_form(Tag.보조용언, "하").if_not_spaced()
    .msg("'~게/케 하다'로 띄어 써야 합니다.").build(),
    
    *rule()
    .id("VX_려 들다_띄어쓰기")
    .tag_form(Tag.연결어미, "려")
    .tag_form(Tag.보조용언, "들").if_not_spaced()
    .msg("'~려 들다'로 띄어 써야 합니다.").build(),

    *rule()
    .id("VX_곤 하다_띄어쓰기")
    .tags({Tag.동사, Tag.동사규칙활용, Tag.동사불규칙활용, Tag.동사파생접미사})
    .tag_form(Tag.연결어미, "곤")
    .tag_form(Tag.보조용언, "하").if_not_spaced()
    .msg('\'merge(({dform[0]}, {dtag[0]}), ("곤", "연결어미")) 하다\'로 띄어 써야 합니다.').build(),

    *rule()
    .id("VX_지 않다_띄어쓰기")
    .tag_form(Tag.연결어미, "지")
    .tag_form(Tag.보조용언, "않").if_not_spaced()
    .msg("'~지 않다'로 띄어 써야 합니다.").build(),
]

_있다_없다_띄어쓰기_set = {"인기", "필요", "품위", "가치", "자비", "자신", "면목", "관심", "부담", "실력", "인망", "의미", "눈치"}

_VA = [    
    *rule()
    .AND(tag(Tag.일반명사), forms({"걱정", "소리", "겁", "죄", "싸가지", "후회", "중복"}))
    .OR(tag_form(Tag.형용사, "없"), tag_form(Tag.일반부사, "없이")).if_not_spaced()
    .msg("'{dform[0]} 없다'로 띄어 써야 합니다.").build(),

    *rule()
    .NOT(tag(Tag.관형사)).context()
    .forms({"꼼짝", "쓸데", "문제", "빈틈", "온데간데", "꾸밈", "스스럼", "부질", "재미", "소용", "틀림", "쓸데", "끊임", "다름", "염치", "빈틈", "정신", "다름", "변함", "끄떡", "문제", "어처구니", "인정사정", "어이", "유례", "끝", "터무니"})
    .OR(tag_form(Tag.형용사, "없"), tag_form(Tag.일반부사, "없이")).if_spaced()
    .msg("'{form[0]}없다'로 붙여 써야 합니다.").build(),

    *rule()
    .NOT(tag(Tag.관형사)).context()
    .forms(_있다_없다_띄어쓰기_set)
    .OR(tag_form(Tag.형용사, "없"), tag_form(Tag.일반부사, "없이")).if_not_spaced()
    .msg("'{form[0]} 없다'로 띄어 써야 합니다.").build(),

    *rule()
    .forms(_있다_없다_띄어쓰기_set)
    .tag_form(Tag.동사, "있").if_not_spaced()
    .msg("'{form[0]} 있다'로 띄어 써야 합니다.").build(),
    
    *rule()
    .NOT(tags({Tag.관형사형전성어미, Tag.형용사파생접미사, Tag.관형격조사, Tag.접속조사})).context()
    .AND(tag(Tag.일반명사), forms({"불", "굴뚝", "주옥", "실낱", "뚱딴지", "철통", "벼락", "목석", "꿈", "쏜살", "한결", "감쪽", "불꽃", "찰떡", "악착", "철벽"}))
    .tag_form(Tag.형용사, "같").if_spaced()
    .msg("비유적 표현인 경우, '{form[0]}같다'로 붙여 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.일반명사, "힘")
    .OR(tag_form(Tag.형용사, "없"), tag_form(Tag.일반부사, "없이")).if_spaced()
    .msg("'힘없다'로 붙여 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.일반명사, "꼴")
    .tag_form(Tag.형용사, "좋").if_spaced()
    .msg("'꼴좋다'로 붙여 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.대명사, "머")
    .tag_form(Tag.긍정지정사, "이")
    .tag_form(Tag.연결어미, "지")
    .tag_form(Tag.보조용언, "않").if_spaced()
    .msg("'머지않다'로 붙여 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.일반부사, "못")
    .tag_form(Tag.형용사파생접미사, "하")
    .tag_form(Tag.연결어미, "지")
    .tag_form(Tag.보조용언, "않").if_spaced()
    .msg("'못지않다'로 붙여 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.일반명사, "사이")
    .tag_form(Tag.형용사, "좋").if_spaced()
    .msg("'사이좋다'로 붙여 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.일반명사, "마지")
    .tag_form(Tag.일반부사, "못").if_spaced()
    .tag_form(Tag.동사파생접미사, "하")
    .msg("'마지못하다'로 붙여 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.일반부사, "너무")
    .tag_form(Tag.동사, "하").if_spaced()
    .msg("'정도가 심하다'의 의미인 경우 '너무하다'로 붙여 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.일반명사, "배")
    .tag_form(Tag.형용사, "부르").if_spaced()
    .msg("'배부르다'로 붙여 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.형용사불규칙활용, "좁")
    .tag_form(Tag.연결어미, "어")
    .tag_form(Tag.동사, "터지").if_spaced()
    .msg("'좁아터지다'로 붙여 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.어근, "그럴싸")
    .AND(tags({Tag.형용사파생접미사, Tag.동사}), form("하")).if_spaced()
    .msg("'그럴싸하다'로 붙여 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.형용사, "약")
    .tag_form(Tag.연결어미, "어")
    .tag_form(Tag.보조용언, "빠지").if_spaced()
    .msg("'약아빠지다'로 붙여 써야 합니다.").build(),

    *rule()
    .tag_form(Tag.일반부사, "못")
    .tag_form(Tag.형용사파생접미사, "되").if_not_spaced()
    .tag_form(Tag.연결어미, "어").if_not_spaced()
    .tag_form(Tag.보조용언,"먹").if_not_spaced()
    .msg("'못돼 먹다' 또는 '못 돼먹다'로 띄어 써야 합니다.").build(),

    *rule()
    .tag(Tag.일반명사)
    .tag_form(Tag.형용사, "어리").if_not_spaced()
    .msg("'{dform[0]} 어리다'로 띄어 써야 합니다.").build(),

    *rule()
    .tag_form(Tag.일반명사, "질")
    .AND(tag(Tag.형용사), forms({"나쁘", "좋"})).if_not_spaced()
    .msg("'질 {form[1]}다'로 띄어 써야 합니다.").build(),

    *rule()
    .id("VA_명사_깊다_띄어쓰기")
    .tag(Tag.일반명사)
    .tag_form(Tag.형용사, "깊").if_not_spaced()
    .msg("'{dform[0]} 깊다'로 띄어 써야 합니다.").build(),
    
    *rule()
    .id("VA_형용사_어하다_붙여쓰기")
    .AND(tags({Tag.형용사, Tag.형용사규칙활용, Tag.형용사불규칙활용, Tag.형용사파생접미사규칙활용}), NOT(form("있")))
    .tag_form(Tag.연결어미, "어")
    .tag_form(Tag.보조용언, "하").if_spaced()
    .msg('\'merge(({dform[0]}, {dtag[0]}), ("어", "연결어미"), ("하", "보조용언"), ("다", "종결어미"))\'로 붙여 써야 합니다.').build(),

    *rule()
    .id("VA_엄청나다_붙여쓰기")
    .tag_form(Tag.일반부사, "엄청")
    .tag_form(Tag.동사, "나").if_spaced()
    .msg("'엄청나다'로 붙여 써야 합니다.").build(),
    
    *rule()
    .id("VA_귀신같다_붙여쓰기")
    .tag_form(Tag.일반명사, "귀신")
    .tag_form(Tag.형용사, "같").if_spaced()
    .msg("'능력이 뛰어나다'의 의미인 경우, '귀신같다'로 붙여 써야 합니다.").build(),
]

_NNG_VA = [
    # 붙여 써야 하는 것
    *NNG_and_some("그지", "없", "형용사", SpacingRule.ATTACHED),
    *NNG_and_some("뜻", "깊", "형용사", SpacingRule.ATTACHED),

    # 띄어 써야 하는 것
    *NNG_and_some("예의", "바르", "형용사", SpacingRule.SPACED),
    *NNG_and_some("골치", "아프", "형용사", SpacingRule.SPACED),
]

_VCP = [
    *rule()
    .id("VCP_이다_선어말어미_붙여쓰기")
    .tag(Tag.긍정지정사).if_spaced()
    .tag_form(Tag.선어말어미, "었")
    .msg("'이었/였'을 앞 말에 붙여 써야 합니다.").build(),
    
    *rule()
    .id("VCP_보조사_이다_붙여쓰기")
    .tag(Tag.보조사).context()
    .tag(Tag.긍정지정사).if_spaced()
    .tag(Tag.종결어미)
    .msg('\'merge(("이", "긍정지정사"), ({dform[1]}, "종결어미"))\'batchim("을", "를") 앞 말에 붙여 써야 합니다.').build(),
]

_MM = [
    *rule()
    .tag_form(Tag.관형사, "무슨")
    .NOT(tags({Tag.여는부호, Tag.닫는부호, Tag.종결부호, Tag.구분부호, Tag.인용부호괄호, Tag.기타특수문자, Tag.줄임표})).if_not_spaced()
    .msg("'무슨 {dform[1]}'batchim(\"으로\", \"로\") 띄어 써야 합니다.").build(),
]

_MAG = [
    *rule()
    .tags({Tag.일반명사, Tag.고유명사, Tag.의존명사})
    .tag_form(Tag.일반부사, "내내").if_not_spaced()
    .msg("'{dform[0]} 내내'로 띄어 써야 합니다.").build(),
    
    *rule()
    .id("MAG_한번_붙여쓰기")
    .NOT(form("다시")).context()
    .tag_form(Tag.관형사, "한")
    .tag_form(Tag.의존명사, "번").if_spaced()
    .NOT(form("더")).context()
    .NOT(form("더")).opt().context()
    .NOT(form("더")).opt().context()
    .AND(tag(Tag.연결어미), forms({"면", "으면"})).context()
    .msg("'한번 ~하면'의 형태가 쓰였을 경우에는 '한번'을 붙여 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.관형사, "한")
    .tag_form(Tag.의존명사, "번").if_spaced()
    .NOT(form("더")).context()
    .NOT(form("더")).opt().context()
    .NOT(form("더")).opt().context()
    .tag_form(Tag.보조용언, "두").context()
    .tag_form(Tag.연결어미, "어서").context()
    .msg("'한번 ~하면'의 형태가 쓰였을 경우에는 '한번'을 붙여 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.일반부사, "더욱")
    .tag_form(Tag.일반부사, "더").if_spaced()
    .msg("'더욱더'로 붙여 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.일반부사, "바로")
    .tag_form(Tag.일반부사, "바로").if_spaced()
    .msg("'바로바로'로 붙여 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.일반부사, "모두")
    .tag_form(Tag.일반부사, "모두").if_not_spaced()
    .msg("'모두 모두'로 띄어 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.동사, "이러")
    .tag_form(Tag.연결어미, "나")
    .tag_form(Tag.동사, "저러").if_spaced()
    .tag_form(Tag.연결어미, "나")
    .msg("'이러나저러나'로 붙여 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.일반부사, "곤드레")
    .tag_form(Tag.일반명사, "만드레").if_spaced()
    .msg("'곤드레만드레'로 붙여 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.일반부사, "기우뚱")
    .tag_form(Tag.일반부사, "기우뚱").if_spaced()
    .msg("'기우뚱기우뚱'으로 붙여 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.연결어미, "지")
    .tag_form(Tag.일반부사, "못").if_not_spaced()
    .msg("'~지 못하다'로 띄어 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.연결어미, "다")
    .tag_form(Tag.보조용언, "못하").if_not_spaced()
    .msg("'~다 못하다'로 띄어 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.일반명사, "밤낮")
    .tag_form(Tag.일반부사, "없이").if_spaced()
    .msg("'밤낮없이'로 붙여 써야 합니다.").build(),

    *rule()
    .tag_form(Tag.동사, "하")
    .tag_form(Tag.연결어미, "다")
    .tag_form(Tag.일반부사, "못").if_spaced()
    .tag_form(Tag.동사파생접미사, "하")
    .tag_form(Tag.연결어미, "어")
    .msg("'하다못해'로 붙여 써야 합니다.").build(),

    *rule()
    .tags({Tag.목적격조사, Tag.보조사}).context()
    .tag_form(Tag.일반부사, "못")
    .AND(tag(Tag.동사), NOT(form("하"))).if_not_spaced()
    .msg("'못 merge(({dform[1]}, {dtag[1]}), (\"다\", \"종결어미\"))'로 띄어 써야 합니다.").build(),

    *rule()
    .AND(tag(Tag.일반명사), forms({"맘", "마음"}))
    .tag_form(Tag.일반부사, "편히").if_not_spaced()
    .msg("'{dform[0]} 편히'로 띄어 써야 합니다.").build(),
    
    *rule()
    .id("MAG_다 같이_띄어쓰기")
    .tag_form(Tag.일반부사, "다")
    .tag_form(Tag.일반부사, "같이").if_not_spaced()
    .msg("'다 같이'로 띄어 써야 합니다.").build(),

    *rule()
    .id("MAG_못다_붙여쓰기")
    .tag_form(Tag.일반부사, "못")
    .tag_form(Tag.일반부사, "다").if_spaced()
    .tags({Tag.동사, Tag.동사규칙활용, Tag.동사불규칙활용}).context().if_spaced()
    .msg("'못다'로 붙여 써야 합니다.").build(),

    *rule()
    .id("MAG_못다_뒤_띄어쓰기")
    .id("MAG_못다_붙여쓰기")
    .tag_form(Tag.일반부사, "못")
    .tag_form(Tag.일반부사, "다").if_spaced()
    .tags({Tag.동사, Tag.동사규칙활용, Tag.동사불규칙활용}).if_not_spaced()
    .msg('\'못다 merge(({dform[2]}, {dtag[2]}), ("다", "종결어미"))\'로 붙여 써야 합니다.').build(),
]

_JX = [
    *rule()
    .id("JX_복합어_보조용언_띄어쓰기")
    .AND(tag(Tag.일반명사), longer(2)).context()
    .tag(Tag.닫는부호).opt().context()
    .tag(Tag.동사파생접미사).context().if_not_spaced()
    .tag(Tag.연결어미).context()
    .AND(tag(Tag.보조용언), forms({"가", "내", "놓", "달", "두", "드리", "버리", "보", "오", "있", "주", "하"})).if_not_spaced()
    .msg("보조 용언 'merge(({form[0]}, \"보조용언\"), (\"다\", \"종결어미\"))'를 앞 말과 띄어 써야 합니다.")
    .detail("보조용언은 앞 말과 붙여 씀이 허용됩니다. 그러나 본용언이 3음절 이상의 복합어인 경우에는 반드시 띄어 써야 합니다.\n예를 들어 '이해해 보다'는 '이해하다'가 '이해+하다'로 이루어진 복합어이므로, 뒤에 오는 보조용언은 반드시 띄어 써야 합니다.")
    .build(),

    *rule()
    .tags(TagGroup.체언)
    .tag_form(Tag.보조사, "밖에").if_spaced()
    .msg("'{dform[0]}밖에'로 붙여 써야 합니다.").build(),
    
    *rule()
    .tags(TagGroup.체언)
    .tag_form(Tag.보조사, "조차").if_spaced()
    .msg("'{dform[0]}조차'로 붙여 써야 합니다.").build(),
    
    *rule()
    .tags(TagGroup.체언).context()
    .AND(tag(Tag.보조사), forms({"야", "이야"}))
    .form("말").if_spaced()
    .form("로")
    .msg("'~야말로'로 붙여 써야 합니다.").build(),
    
    *rule()
    .tag(Tag.관형사형전성어미)
    .tag_form(Tag.일반명사, "때").if_not_spaced()
    .msg("'때'를 앞 말과 띄어 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.일반명사, "시")
    .tag_form(Tag.보조사, "도")
    .tag_form(Tag.일반명사, "때").if_not_spaced()
    .tag_form(Tag.보조사, "도")
    .msg("'시도 때도'로 띄어 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.연결어미, "게")
    .tag_form(Tag.보조사, "나마").if_spaced()
    .msg("'~게나마'로 붙여 써야 합니다.").build(),

    *rule()
    .id("JX_깨나_붙여쓰기")
    .tag(Tag.일반명사)
    .tag_form(Tag.보조사, "깨나").if_spaced()
    .msg("'{dform[0]}깨나'로 붙여 써야 합니다.").build(),

    *rule()
    .id("JX_치고_붙여쓰기")
    .tags({Tag.일반명사, Tag.고유명사, Tag.명사형전성어미, Tag.대명사, Tag.의존명사}).context()
    .tag_form(Tag.보조사, "치고").if_spaced()
    .msg("'치고'를 앞 말에 붙여 써야 합니다.").build(),

    *rule()
    .id("JX_만_붙여쓰기")
    .tags({Tag.일반명사, Tag.고유명사, Tag.명사형전성어미, Tag.대명사, Tag.의존명사}).context()
    .tag_form(Tag.보조사, "만").if_spaced()
    .msg("'~정도'의 의미인 경우, '만'을 앞 말에 붙여 써야 합니다.").build(),

    *rule()
    .id("JX_마다_붙여쓰기")
    .tags({Tag.일반명사, Tag.고유명사, Tag.명사형전성어미, Tag.대명사, Tag.의존명사}).context()
    .tag_form(Tag.보조사, "마다").if_spaced()
    .msg("'마다'를 앞 말에 붙여 써야 합니다.").build(),

    *rule()
    .id("JX_까지_붙여쓰기")
    .tags({Tag.일반명사, Tag.고유명사, Tag.명사형전성어미, Tag.대명사, Tag.의존명사}).context()
    .tag_form(Tag.보조사, "까지").if_spaced()
    .msg("'까지'를 앞 말에 붙여 써야 합니다.").build(),
]

_JKB = [
    *rule()
    .id("JKB_처럼_붙여쓰기")
    .tag_form(Tag.부사격조사, "처럼").if_spaced()
    .msg("'처럼'을 앞 말에 붙여 써야 합니다.").build(),
    
    *rule()
    .id("JKB_보다_붙여쓰기")
    .tags({Tag.명사형전성어미, Tag.대명사, Tag.일반명사, Tag.고유명사, Tag.명사파생접미사}).context()
    .tag_form(Tag.부사격조사, "보다").if_spaced()
    .msg("비교의 의미인 '보다'는 앞 말에 붙여 써야 합니다.").build(),
    
    *rule()
    .id("JKB_으로_붙여쓰기")
    .tag_form(Tag.부사격조사, "으로").if_spaced()
    .msg("'으로'를 앞 말에 붙여 써야 합니다.").build(),

    *rule()
    .id("JKB_에서_붙여쓰기")
    .tag_form(Tag.부사격조사, "에서").if_spaced()
    .msg("'에서'를 앞 말에 붙여 써야 합니다.").build(),

    *rule()
    .id("JKB_보고_붙여쓰기")
    .tag_form(Tag.부사격조사, "보고").if_spaced()
    .msg("'에게'의 의미인 경우, '보고'를 앞 말에 붙여 써야 합니다.").build(),
]

_EF = [
    *rule()
    .NOT(tags({Tag.여는부호, Tag.닫는부호, Tag.종결부호, Tag.구분부호, Tag.인용부호괄호, Tag.기타특수문자})).context()
    .tag(Tag.종결어미).if_spaced()
    .msg("어미를 앞 말에 붙여 써야 합니다.").build(),
    
    *rule()
    .AND(tag(Tag.관형사형전성어미), forms({"라는", "다는", "는"}))
    .form("군").if_spaced()
    .msg("'-군'은 어미이므로, 앞 말에 붙여 써야 합니다.").build(),
    
    *rule()
    .AND(tag(Tag.연결어미), forms({"는군", "군"}))
    .tag_form(Tag.감탄사, "그래").if_spaced()
    .msg("'~군 뒤의 '그래'는 어미이므로 앞 말과 붙여 써야 합니다.").build(),
    
    *rule()
    .id("EF_잖아_붙여쓰기")
    .tags({Tag.대명사, Tag.일반명사, Tag.고유명사})
    .tag(Tag.긍정지정사).if_spaced()
    .tag_form(Tag.종결어미, "잖아")
    .msg("'{dform[0]}잖아'로 붙여 써야 합니다.").build(),
    
    *rule()
    .id("EF_인가요_붙여쓰기")
    .tags({Tag.대명사, Tag.일반명사, Tag.명사파생접미사, Tag.명사형전성어미}).context()
    .tag(Tag.긍정지정사)
    .tag_form(Tag.관형사형전성어미, "ᆫ")
    .tag_form(Tag.동사, "가").if_spaced()
    .tag_form(Tag.종결어미, "어요")
    .msg("'~인가요'를 앞 말에 붙여 써야 합니다.").build(),
]

_EC = [
    *rule()
    .tag_form(Tag.연결어미, "자")
    .form("마").if_spaced()
    .tag_form(Tag.연결어미, "자")
    .msg("'-자마자'로 붙여 써야 합니다. (예: 버튼을 누르자마자)").build(),
    
    *rule()
    .tag_form(Tag.의존명사, "거")
    .tag(Tag.긍정지정사).if_spaced()
    .AND(tag(Tag.연결어미), forms({"라고", "래서"}))
    .msg("'~래서', '랬'을 앞 말에 붙여 써야 합니다.").build(),
    
    *rule()
    .tag(Tag.긍정지정사)
    .tag_form(Tag.관형사형전성어미, "ᆯ")
    .form("수록").if_spaced()
    .msg("'~일수록'으로 붙여 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.보조사, "거나").if_spaced()
    .msg("'~거나'를 앞 말에 붙여 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.형용사규칙활용, "곱")
    .tag_form(Tag.연결어미, "디")
    .tag_form(Tag.형용사규칙활용, "곱").if_spaced()
    .msg("'곱디곱다'로 붙여 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.형용사, "차")
    .tag_form(Tag.연결어미, "디")
    .tag_form(Tag.형용사, "차").if_spaced()
    .msg("'차디차다'로 붙여 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.형용사, "크")
    .tag_form(Tag.연결어미, "디")
    .tag_form(Tag.형용사, "크").if_spaced()
    .msg("'크디크다'로 붙여 써야 합니다.").build(),
    
    *rule()
    .id("EC_고서_붙여쓰기")
    .tag_form(Tag.동사파생접미사, "하")
    .tag_form(Tag.연결어미, "고")
    .tag_form(Tag.부사격조사, "서").if_spaced()
    .any().opt()
    .tag_form(Tag.연결어미, "라도")
    .msg("'~하고서라도'로 붙여 써야 합니다.").build(),
    
    *rule()
    .id("EC_ㄹ수록_붙여쓰기")
    .tags({Tag.동사, Tag.동사규칙활용, Tag.동사불규칙활용, Tag.형용사, Tag.형용사규칙활용, Tag.형용사불규칙활용})
    .tag_form(Tag.관형사형전성어미, "ᆯ")
    .tag_form(Tag.일반명사, "수록").if_spaced()
    .msg("'merge(({dform[0]}, {dtag[0]}), (\"ᆯ수록\", \"연결어미\"))'batchim(\"으로\", \"로\") 붙여 써야 합니다.").build(),

    *rule()
    .id("EC_ㄴ들_붙여쓰기")
    .tags(TagGroup.용언 | {Tag.긍정지정사})
    .tag_form(Tag.관형사형전성어미, "ᆫ")
    .tag_form(Tag.일반명사, "들").if_spaced()
    .NOT(tags(TagGroup.조사)).context()
    .msg('\'~다고 할지라도\'의 의미인 경우, \'merge(({dform[0]}, {dtag[0]}), ("ᆫ들", "연결어미"))\'로 붙여 써야 합니다.').build(),

    *rule()
    .id("EC_ㄴ들_선어말어미_붙여쓰기")
    .tags(TagGroup.용언 | {Tag.긍정지정사})
    .tag(Tag.선어말어미)
    .tag_form(Tag.관형사형전성어미, "ᆫ")
    .tag_form(Tag.일반명사, "들").if_spaced()
    .NOT(tags(TagGroup.조사)).context()
    .msg('\'~다고 할지라도\'의 의미인 경우, \'merge(({dform[0]}, {dtag[0]}), ({dform[1]}, "선어말어미"), ("ᆫ들", "연결어미"))\'로 붙여 써야 합니다.').build(),

    *rule()
    .id("EC_은들_붙여쓰기")
    .tags(TagGroup.용언 | {Tag.긍정지정사})
    .tag_form(Tag.관형사형전성어미, "은")
    .tag_form(Tag.일반명사, "들").if_spaced()
    .NOT(tags(TagGroup.조사)).context()
    .msg('\'~다고 할지라도\'의 의미인 경우, \'merge(({dform[0]}, {dtag[0]}), ("은들", "연결어미"))\'로 붙여 써야 합니다.').build(),

    *rule()
    .id("EC_라 한들_붙여쓰기")
    .tag_form(Tag.긍정지정사, "이").context()
    .tag_form(Tag.연결어미, "라").context()
    .tag_form(Tag.관형사, "한")
    .tag_form(Tag.일반명사, "들").if_spaced()
    .msg("'~다고 할지라도'의 의미인 경우, '~한들'로 붙여 써야 합니다.").build(),

    *rule()
    .id("EC_ㄹ수록_붙여쓰기")
    .tag_form(Tag.관형사형전성어미, "ᆯ")
    .form("수록").if_spaced()
    .msg("'ㄹ수록'은 어미이므로 앞 말에 붙여 써야 합니다. (예: 하면 할수록)").build(),
]

_ETN = [
    *rule()
    .id("ETN_시기")
    .tag_form(Tag.선어말어미, "시")
    .tag_form(Tag.명사형전성어미, "기").if_spaced()
    .NOT(tag_form(Tag.목적격조사, "ᆯ")).context()
    .msg("'-시기'로 붙여 써야 합니다.").build(),
    
    *rule()
    .id("ETN_시길")
    .tag_form(Tag.선어말어미, "시")
    .tag_form(Tag.명사형전성어미, "기").if_spaced()
    .tag_form(Tag.목적격조사, "ᆯ")
    .msg("'-시길'로 붙여 써야 합니다.").build(),
]

_ETM = [
    *rule()
    .tags({Tag.일반명사, Tag.고유명사, Tag.명사파생접미사, Tag.대명사})
    .tag_form(Tag.형용사, "같").if_not_spaced()
    .msg("'같다'를 앞 말과 띄어 써야 합니다.").build(),
    
    *rule()
    .id("ETM_ㄴ다는_붙여쓰기")
    .any()
    .tag(Tag.관형사형전성어미)
    .tag_form(Tag.관형사형전성어미, "다는").if_spaced()
    .msg('\'merge(({dform[0]}, {dtag[0]}), ({dform[1]}, {dtag[1]}), ("다는", "관형사형전성어미"))\'으로 붙여 써야 합니다.').build(),
]

_XSA = [
    *rule()
    .NOT(tags({Tag.종결부호, Tag.줄임표}))
    .tag_form(Tag.형용사파생접미사규칙활용, "답").if_spaced()
    .msg("'답다'를 앞 말에 붙여 써야 합니다.").build(),
]

_XSN = [
    *rule()
    .id("XSN_붙여쓰기")
    .AND(tag(Tag.명사파생접미사), forms({"당", "씩", "들", "부", "뻘", "생", "여", "째", "풍", "용"})).if_spaced()
    .msg("'{form[0]}'batchim(\"을\", \"를\") 앞 말과 붙여 써야 합니다.").build(),

    *rule()
    .tag_form(Tag.일반명사, "며칠")
    .tag_form(Tag.명사파생접미사, "째").if_spaced()
    .msg("'며칠째'로 붙여 써야 합니다.").build(),
    
    *rule()
    .tag_form(Tag.일반부사, "언제")
    .form("적").if_not_spaced()
    .msg("'언제 적'으로 띄어 써야 합니다.").build(),

    *rule()
    .tag(Tag.명사파생접미사)
    .tag_form(Tag.동사, "당하").if_spaced()
    .msg("'당하다'를 앞 말과 붙여 써야 합니다.").build(),

    *rule()
    .id("XSN_껏_붙여쓰기")
    .tag(Tag.일반명사)
    .tag_form(Tag.명사파생접미사, "껏").if_spaced()
    .msg("'{dform[0]}껏'으로 붙여 써야 합니다.").build(),

    *rule()
    .id("XSN_쯤_붙여쓰기")
    .NOT(tag(Tag.관형사형전성어미)).context()
    .form("쯤").if_spaced()
    .msg("'쯤'을 앞 말에 붙여 써야 합니다.").build(),

    *rule()
    .id("XSN_경_1_붙여쓰기")
    .tag(Tag.숫자)
    .AND(tags({Tag.의존명사, Tag.일반명사}), forms({"년", "세기", "월", "일", "시", "분", "초"}))
    .any()
    .tag_form(Tag.명사파생접미사, "경").if_spaced()
    .msg("'{dform[0]}{form[0]} {dform[2]}경'으로 붙여 써야 합니다.").build(),

    *rule()
    .id("XSN_경_2_붙여쓰기")
    .tag(Tag.숫자)
    .AND(tags({Tag.의존명사, Tag.일반명사}), forms({"년", "세기", "월", "일", "시", "분", "초"}))
    .tag_form(Tag.명사파생접미사, "경").if_spaced()
    .msg("'{dform[0]}{form[0]}경'으로 붙여 써야 합니다.").build(),
    
    *rule()
    .id("XSN_경_3_붙여쓰기")
    .tag(Tag.일련번호)
    .tag_form(Tag.명사파생접미사, "경").if_spaced()
    .msg("'{dform[0]}경'으로 붙여 써야 합니다.").build(),

    *rule()
    .id("XSN_권_붙여쓰기")
    .tag(Tag.숫자)
    .tag_form(Tag.일반명사, "위")
    .tag_form(Tag.명사파생접미사, "권").if_spaced()
    .msg("'{dform[0]}위권'으로 붙여 써야 합니다.").build(),

    *rule()
    .id("XSN_꼴_붙여쓰기")
    .tag(Tag.숫자)
    .AND(tag(Tag.의존명사), forms({"명"}))
    .tag_form(Tag.명사파생접미사, "꼴").if_spaced()
    .msg("'{dform[0]}{form[0]}꼴'로 붙여 써야 합니다.").build(),

    *rule()
    .id("XSN_끼리_붙여쓰기")
    .tags({Tag.일반명사, Tag.명사파생접미사, Tag.대명사}).context()
    .tag_form(Tag.명사파생접미사, "끼리").if_spaced()
    .msg("'끼리'를 앞 말에 붙여 써야 합니다.").build(),

    *rule()
    .id("XSN_별_붙여쓰기")
    .tag_form(Tag.명사파생접미사, "별").if_spaced()
    .tag_form(Tag.부사격조사, "로").context()
    .msg("'별'을 앞 말에 붙여 써야 합니다.").build(),

    *rule()
    .id("XSN_화_1_붙여쓰기")
    .tags({Tag.일반명사, Tag.고유명사}).context()
    .tag_form(Tag.명사파생접미사, "화").if_spaced()
    .tag_form(Tag.동사파생접미사, "하").context()
    .msg("'화'를 앞 말에 붙여 써야 합니다.").build(),

    *rule()
    .id("XSN_화_2_붙여쓰기")
    .tags({Tag.일반명사, Tag.고유명사}).context()
    .tag_form(Tag.명사파생접미사, "화").if_spaced()
    .tags({Tag.부사격조사, Tag.목적격조사}).context()
    .msg("'화'를 앞 말에 붙여 써야 합니다.").build(),
]

_XSV = [
    *rule()
    .tag(Tag.일반명사)
    .tag(Tag.명사파생접미사).if_not_spaced()
    .tag_form(Tag.동사파생접미사, "하").if_spaced()
    .msg("'{dform[0]}{dform[1]}하다'로 붙여 써야 합니다.").build(),

    *rule()
    .id("XSV_받다_붙여쓰기")
    .NOT(tag(Tag.관형사형전성어미)).context()
    .AND(tag(Tag.일반명사), forms(받다_ALLOWS))
    .tag_form(Tag.동사불규칙활용, "받").if_spaced()
    .msg("'{dform[0]}받다'로 붙여 써야 합니다.").detail("물리적으로 전달받는 것이 아닌, 어떤 행위의 대상이 됨을 나타낼 때에는 '받다'를 앞 말에 붙여 써야 합니다.\n예를 들어 '평가받다'의 경우, '평가'라는 물건을 받는 것이 아닌 '평가를 당하다'의 의미이므로 '평가받다'로 붙여 씁니다.\n'받다'를 '하다'로 바꿔 써서 말이 된다면, 붙여 씁니다.\n※열받다는 예외적으로 붙여 씁니다.").build(),
]

_SE = [
    *rule()
    .id("SE_뒤_띄어쓰기")
    .any().context()
    .tag(Tag.줄임표).if_not_spaced()
    .tag(Tag.대명사).if_not_spaced()
    .msg("말줄임표 뒤에 띄어쓰기가 없는 것 같습니다.").build(),
]

_IDIOM = [
    *rule()
    .id("IDIOM_듣도 보도 못하다_붙여쓰기")
    .tag_form(Tag.동사규칙활용, "듣")
    .tag_form(Tag.연결어미, "도")
    .tag_form(Tag.동사, "보")
    .tag_form(Tag.연결어미, "도")
    .tag_form(Tag.일반부사, "못")
    .AND(tags({Tag.동사, Tag.보조용언}), form("하")).if_spaced()
    .msg("'듣도 보도 못하다'로 붙여 써야 합니다.").build(),
    
    *rule()
    .id("IDIOM_빼도 박도 못하다_붙여쓰기")
    .tag_form(Tag.동사, "빼")
    .tag_form(Tag.연결어미, "도")
    .tag_form(Tag.동사, "박")
    .tag_form(Tag.연결어미, "도")
    .tag_form(Tag.일반부사, "못")
    .AND(tags({Tag.동사, Tag.보조용언}), form("하")).if_spaced()
    .msg("'빼도 박도 못하다'로 붙여 써야 합니다.").build(),

    *rule()
    .id("IDIOM_~지 못하다_붙여쓰기")
    .tag_form(Tag.연결어미, "지")
    .any().opt()
    .any().opt()
    .tag_form(Tag.일반부사, "못")
    .tag_form(Tag.동사, "하").if_spaced()
    .msg("'~지 못하다'로 붙여 써야 합니다.").build(),
]

_WORD_3 = [
    *word_3("기분", Tag.일반명사, "전환", Tag.일반명사,"하", Tag.동사파생접미사, spacing_rule=SpacingRule.SPACED, message="기분 전환 하다"),
    *word_3("특별", Tag.일반명사, "취급", Tag.일반명사,"하", Tag.동사파생접미사, spacing_rule=SpacingRule.SPACED, message="특별 취급 하다"),
    *word_3("특별", Tag.일반명사, "대우", Tag.일반명사,"하", Tag.동사파생접미사, spacing_rule=SpacingRule.SPACED, message="특별 대우 하다"),
    *word_3("근력", Tag.일반명사, "운동", Tag.일반명사,"하", Tag.동사파생접미사, spacing_rule=SpacingRule.SPACED, message="근력 운동 하다"),
]

_LOANWORDS = [
    *rule()
    .id("노하우_붙여쓰기")
    .tag_form(Tag.일반명사, "노")
    .tag_form(Tag.고유명사, "하우").if_spaced()
    .msg("'노하우'로 붙여 써야 합니다.").build(),
    
    *rule()
    .id("헤어스타일_붙여쓰기")
    .tag_form(Tag.일반명사, "헤어")
    .tag_form(Tag.일반명사, "스타일").if_spaced()
    .msg("'헤어스타일'로 붙여 써야 합니다.").build(),
    
    *rule()
    .id("포비아_붙여쓰기")
    .tags({Tag.고유명사, Tag.일반명사})
    .tag_form(Tag.고유명사, "포비아").if_spaced()
    .msg("'-phobia'는 접미사이므로, 앞 말에 붙여 써야 합니다.").build(),
]

def rule() -> RuleBuilder:
    return RuleBuilder(SpellErrorType.NEED_ML_JUDGE)

_NEED_ML_JUDGE = [
    *rule()
    .id("열받다_띄어쓰기")
    .tag_form(Tag.일반명사, "열")
    .tag_form(Tag.동사불규칙활용, "받").if_spaced()
    .msg("'화나다'의 의미일 경우 '열받다'로 붙여 써야 합니다.").build(),
    
    # 오늘따라 운이 좋네.	오늘 따라 운이 좋네.
    *rule()
    .id("따라_붙여쓰기")
    .tag_form(Tag.동사, "따르").if_spaced()
    .tag_form(Tag.연결어미, "어")
    .msg("'따라'를 앞 말에 붙여 써야 합니다.").build(),    
    
    *rule()
    .id("저세상_붙여쓰기")
    .tag_form(Tag.관형사, "저")
    .tag_form(Tag.일반명사, "세상").if_spaced()
    .msg("'저승'의 의미일 경우 '저세상'으로 붙여 써야 합니다.").build(),
    
    *rule()
    .id("자기주장_붙여쓰기")
    .form("자기")
    .tag_form(Tag.일반명사, "주장").if_spaced()
    .msg("'자기주장'으로 붙여 써야 합니다.").build(),
    
    *rule()
    .id("다하다_붙여쓰기")
    .tag_form(Tag.일반부사, "다")
    .tag_form(Tag.동사파생접미사, "하").if_spaced()
    .msg("'다하다'로 붙여 써야 합니다.").build(),
    
    *rule()
    .id("그럴듯하다_붙여쓰기")
    .tag_form(Tag.형용사규칙활용, "그렇")
    .tag_form(Tag.관형사형전성어미, "ᆯ")
    .tag_form(Tag.의존명사, "듯").if_spaced()
    .msg("'제법 그렇다', '제법 괜찮다'의 의미인 경우 '그럴듯하다'로 붙여 써야 합니다.").build(),

    *rule()
    .id("지켜보다_붙여쓰기")
    .tag_form(Tag.동사, "지키")
    .tag_form(Tag.연결어미, "어")
    .tag_form(Tag.보조용언, "보").if_spaced()
    .msg("'주의깊게 보다'인 경우에는 '지켜보다'로 붙여 써야 합니다.")
    .build(),

    *rule()
    .id("흘러들어 오다_띄어쓰기")
    .tag_form(Tag.동사, "흐르")
    .tag_form(Tag.연결어미, "어")
    .tag_form(Tag.동사, "들어오").if_not_spaced()
    .msg("'흘러들어 오다'로 띄어 써야 합니다.").build(),
]

SPACING_ERRORS = [
    *_SPACING_ERRORS,
    *_NNB,
    *_NNG,
    *_NNG_SINGLE_WORDS,
    *_NNG_NNG,
    *_NR,
    *_VV,
    *_NNG_VV,
    *_VV_EC_VV,
    *_VX,
    *_VA,
    *_NNG_VA,
    *_VCP,
    *_MM,
    *_MAG,
    *_JX,
    *_JKB,
    *_EF,
    *_EC,
    *_ETN,
    *_ETM,
    *_XSA,
    *_XSN,
    *_XSV,
    *_SE,
    *_IDIOM,
    *_WORD_3,
    *_LOANWORDS,
]