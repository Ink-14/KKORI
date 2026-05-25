from src.engines.configs.spell_checker_config_builder import *
from src.models.interface import Tag, TagGroup, SpellErrorType

def rule() -> RuleBuilder:
    return RuleBuilder(SpellErrorType.SPELLING)

_CERTAINS: list[KoSpellRules] = [
    *rule()
    .AND(any_batchim(), NOT(tag(Tag.닫는부호)))
    .tag_form(Tag.긍정지정사, "이")
    .tag_form(Tag.종결어미, "예요")
    .msg("'~이에요'가 올바른 표현입니다.")
    .build(),

    *rule()
    .tag(Tag.부정지정사)
    .tag_form(Tag.종결어미, "예요")
    .msg("'아니에요'가 올바른 표현입니다.")
    .build(),

    *rule()
    .tag_form(Tag.동사, "있")
    .tag_form(Tag.선어말어미, "엇")
    .msg("'있었다'의 오타입니다.")
    .build(),

    *rule()
    .tag_form(Tag.일반명사, "머리")
    .tag_form(Tag.일반명사, "속")
    .msg("'머릿속'이 올바른 표현입니다.")
    .build(),

    *rule()
    .batchim("ᆯ")
    .AND(tags(TagGroup.조사), form("으로"))
    .msg("받침이 ᆯ인 단어에는 '로'를 써야 합니다.")
    .build(),

    *rule()
    .tag_form(Tag.보조용언, "계시")
    .tag_form(Tag.종결어미, "군")
    .msg("'계시는군'의 형태로 써야 합니다.")
    .build(),

    *rule()
    .tag_form(Tag.동사, "두르")
    .tag(Tag.연결어미)
    .tag_form(Tag.동사, "쌓이")
    .msg("'둘러싸이다'가 올바른 표현입니다.")
    .build(),

    *rule()
    .batchim("ᆫ")
    .tag_form(Tag.명사파생접미사, "률")
    .msg("ㄴ받침으로 끝나는 명사에는 '율'을 사용해야 합니다.")
    .build(),
    
    *rule()
    .no_batchim()
    .tag_form(Tag.명사파생접미사, "률")
    .msg("받침 없는 명사에는 '율'을 사용해야 합니다.")
    .build(),
    
    *rule()
    .AND(any_batchim(), NOT(batchim("ᆫ")))
    .tag_form(Tag.명사파생접미사, "율")
    .msg("ㄴ받침 이외의 받침 있는 명사에는 '률'을 사용해야 합니다.")
    .build(),

    *rule()
    .tag_form(Tag.형용사파생접미사규칙활용, "스럽")
    .tag_form(Tag.관형사형전성어미, "ᆫ")
    .msg("'~스러운'을 '스런'으로 줄여 쓸 수 없습니다.")
    .build(),

    *rule()
    .tag_form(Tag.형용사규칙활용, "즐겁")
    .tag_form(Tag.관형사형전성어미, "ᆫ")
    .msg("'즐거운'이 올바른 표현입니다.")
    .build(),
    
    *rule()
    .tag_form(Tag.형용사, "서툴")
    .AND(tags({Tag.연결어미, Tag.종결어미}), forms({"어요", "어서", "어도", "어"}))
    .msg('\'merge((\"서투르\", \"동사\"), ({form[1]}, {dtag[1]}))\'batchim("이", "가") 올바른 표현입니다.').build(),

    *rule()
    .tag_form(Tag.동사, "머물")
    .AND(tags({Tag.연결어미, Tag.종결어미}), forms({"어요", "어서", "어도", "어"}))
    .msg('\'merge((\"머무르\", \"동사\"), ({form[1]}, {dtag[1]}))\'batchim("이", "가") 올바른 표현입니다.').build(),

    *rule()
    .tag_form(Tag.형용사, "서둘")
    .AND(tags({Tag.연결어미, Tag.종결어미}), forms({"어요", "어서", "어도", "어"}))
    .msg('\'merge((\"서두르\", \"동사\"), ({form[1]}, {dtag[1]}))\'batchim("이", "가") 올바른 표현입니다.').build(),

    *rule()
    .tag_form(Tag.관형격조사, "의")
    .tag_form(Tag.관형격조사, "의")
    .msg("조사 '의'가 중복으로 사용된 것 같습니다.")
    .build(),
    
    *rule()
    .OR(tag_form(Tag.동사, "하"), tag_form(Tag.동사파생접미사, "하")).context()
    .OR(tag_form(Tag.선어말어미, "었"), tag_form(Tag.선어말어미, "겠")).context()
    .tag_form(Tag.동사, "쓰")
    .AND(tag(Tag.종결어미), forms({"ᆸ니다", "ᆸ니까"}))
    .msg("'습니다'의 오타가 아닌가요?")
    .build(),
    
    *rule()
    .tag_form(Tag.보조용언, "있")
    .tag_form(Tag.선어말어미, "엇")
    .msg("'있었'의 오타가 아닌가요?")
    .build(),
    
    *rule()
    .tag_form(Tag.부정지정사, "아니")
    .tag_form(Tag.선어말어미, "였")
    .msg("'아니었다'가 올바른 표현입니다.")
    .build(),
    
    *rule()
    .tag_form(Tag.부정지정사, "아니")
    .tag_form(Tag.연결어미, "예요")
    .msg("'아니에요'가 올바른 표현입니다.")
    .build(),
    
    *rule()
    .tag_form(Tag.동사, "되")
    .OR(tag_form(Tag.동사, "있"), tag_form(Tag.연결어미, "서")).context()
    .msg("'돼'가 올바른 표현입니다.")
    .build(),
    
    *rule()
    .tag_form(Tag.동사, "되")
    .tag_form(Tag.종결어미, "어")
    .tag_form(Tag.인용격조사, "라고")
    .msg("'되라고'의 오타가 아닌가요?")
    .build(),
    
    *rule()
    .AND(tag(Tag.동사), forms({"헤어나", "벗어나"}))
    .tag_form(Tag.선어말어미, "엇")
    .msg("'어났'의 오타가 아닌가요?")
    .build(),
    
    *rule()
    .tag_form(Tag.보조용언, "않")
    .tag_form(Tag.동사, "되")
    .msg("'안 돼'의 오타가 아닌가요?")
    .build(),

    *rule()
    .tag_form(Tag.일반명사, "끈")
    .tag_form(Tag.주격조사, "이")
    .tag_form(Tag.명사형전성어미, "ᆷ")
    .OR(tag_form(Tag.일반부사, "없이"), tag_form(Tag.형용사, "없"))
    .msg("'끊임없이'의 오타가 아닌가요?")
    .build(),
    
    *rule()
    .AND(tag(Tag.일반명사), forms({"재미", "상관", "관심", "흥미"}))
    .form("잇")
    .msg("'있다'의 오타가 아닌가요?")
    .build(),
    
    *rule()
    .tag_form(Tag.동사, "간지르")
    .msg("'간질이다'가 올바른 표현입니다. 예: 간질임, 간질이다 등")
    .build(),
    
    *rule()
    .tag_form(Tag.관형사, "왠")
    .msg("'웬'이 올바른 표현입니다.")
    .build(),
    
    *rule()
    .tag_form(Tag.일반부사, "웬지")
    .msg("'왠지'가 올바른 표현입니다.")
    .build(),
    
    *rule()
    .tag_form(Tag.일반부사, "어따")
    .tag_form(Tag.동사, "대")
    .tag_form(Tag.연결어미, "고")
    .msg("'얻다 대고'가 올바른 표현입니다.")
    .build(),

    *rule()
    .OR(tag_form(Tag.동사, "헤매이"), tag_form(Tag.동사, "헤메"))
    .msg("'헤매다'가 올바른 표현입니다.")
    .build(),

    *rule()
    .tag_form(Tag.동사파생접미사, "하")
    .tag_form(Tag.연결어미, "어")
    .tag_form(Tag.동사, "매")
    .msg("'헤매다'가 올바른 표현입니다.")
    .build(),

    *rule()
    .tag_form(Tag.동사, "떼우")
    .msg("'때우다'의 오타가 아닌가요?")
    .build(),

    *rule()
    .AND(tag(Tag.형용사), forms({"어줍잖", "어쭙찮", "어줍찮", "어쭙찮"}))
    .msg("'어쭙잖다'가 올바른 표현입니다.")
    .build(),
    
    *rule()
    .tag(Tag.일반명사)
    .tag_form(Tag.종결어미, "습니다")
    .msg("'습니다' 앞에 '했', 또는 '됐'이 누락되지 않았나요?")
    .build(),
]

_OM = [
    *rule()
    .tag_form(Tag.동사, "뿜")
    .tag_form(Tag.연결어미, "어")
    .tag_form(Tag.동사, "나오")
    .msg("'뿜어져 나오다'로 써야 합니다.")
    .build(),

    *rule()
    .tag_form(Tag.일반부사, "안절부절")
    .tag_form(Tag.동사, "하")
    .msg("'안절부절못하다'가 올바른 표현입니다.")
    .build(),

    *rule()
    .tag_form(Tag.일반명사, "가능")
    .tag_form(Tag.형용사파생접미사, "하")
    .tag_form(Tag.관형사형전성어미, "ᆫ")
    .tag(Tag.일반부사)
    .msg("'가능한 한~'으로 써야 합니다.")
    .build(),
    
    *rule()
    .tag_form(Tag.동사, "쥐이")
    .tag_form(Tag.연결어미, "어")
    .tag_form(Tag.보조용언, "있")
    .msg("'쥐어져 있다'가 올바른 표현입니다.")
    .build(),

    *rule()
    .id("OM_넣었다 빼다")
    .tag_form(Tag.동사, "넣")
    .tag_form(Tag.연결어미, "다")
    .tag_form(Tag.동사, "빼").if_not_spaced()
    .msg("'넣었다 빼다'가 올바른 표현입니다.").build(),

    *rule()
    .tag(Tag.일반명사)
    .tag_form(Tag.연결어미, "으니")
    .msg("오타가 아닌가요?")
    .build(),
]

_ADD = [
    *rule()
    .tag_form(Tag.형용사, "힘들")
    .tag_form(Tag.연결어미, "으며")
    .msg("불필요한 '으'가 사용되었습니다.")
    .build(),

    *rule()
    .tags({Tag.동사, Tag.동사규칙활용, Tag.동사불규칙활용, Tag.동사파생접미사, Tag.보조용언})
    .tag_form(Tag.연결어미, "ᆯ려고")
    .NOT(tag_form(Tag.보조용언, "하")).context()
    .NOT(tag_form(Tag.연결어미, "어야")).context()
    .msg("'merge(({dform[0]}, {dtag[0]}), (\"려고\", \"연결어미\"))'가 올바른 표현입니다.")
    .build(),

    *rule()
    .tag_form(Tag.동사, "삼가하")
    .msg("'삼가다'가 올바른 표현입니다.")
    .build(),
    
    *rule()
    .tag_form(Tag.형용사규칙활용, "누렇")
    .tag_form(Tag.종결어미, "네")
    .msg("'누러네'로 써야 합니다.")
    .build(),

    *rule()
    .tag_form(Tag.동사, "되뇌이")
    .any()
    .msg("'merge((\"되뇌\", \"동사\"), ({dform[1]}, {dtag[1]}))'batchim(\"이\", \"가\") 올바른 표현입니다.")
    .build(),

    *rule()
    .tag_form(Tag.동사, "들이키")
    .msg("(물 등을) '들이켜다'가 올바른 표현입니다.")
    .build(),

    *rule()
    .tag_form(Tag.동사, "캥기")
    .msg("'켕기다'가 올바른 표현입니다.")
    .build(),

    *rule()
    .form("수두룩")
    .form("빽빽")
    .msg("'수두룩'이 올바른 표현입니다.('빽빽' 불필요)")
    .build(),

    *rule()
    .form("끄덕")
    .form("없")
    .msg("'끄떡없다'의 오타가 아닌가요?")
    .build(),

    *rule()
    .tag_form(Tag.동사, "시뻘개지")
    .msg("'시뻘게지다'가 올바른 표현입니다.")
    .build(),

    *rule()
    .form("어리버리")
    .msg("'어리바리'가 올바른 표현입니다.")
    .build(),

    *rule()
    .tag_form(Tag.일반명사, "염치")
    .form("불구")
    .msg("'염치 불고(不顧)'가 올바른 표현입니다.")
    .build(),

    *rule()
    .tag_form(Tag.동사, "꽃히")
    .msg("'꽂다'의 오기가 아닌지요?")
    .build(),

    *rule()
    .tag_form(Tag.일반명사, "열")
    .tag_form(Tag.동사, "띄")
    .any()
    .msg("'merge((\"열띠\", \"형용사\"), ({dform[2]}, {dtag[2]}))'batchim(\"이\", \"가\") 올바른 표현입니다.")
    .build(),
    
    *rule()
    .tag_form(Tag.동사, "잊히")
    .tag_form(Tag.연결어미, "어")
    .tag_form(Tag.보조용언, "지")
    .any()
    .msg("'잊혀지다'는 이중 피동 표현이므로 'merge((\"잊히\", \"동사\"), ({dform[3]}, {dtag[3]}))'batchim(\"으로\", \"로\") 쓸 것을 권장합니다.")
    .build(),
    
    *rule()
    .tag_form(Tag.동사, "불리우")
    .any()
    .msg("'불리우다'는 이중 피동 표현이므로 'merge((\"불리\", \"동사\"), ({dform[1]}, {dtag[1]}))'batchim(\"으로\", \"로\") 쓸 것을 권장합니다.")
    .build(),
    
    *rule()
    .tag_form(Tag.동사, "쓰이")
    .tag_form(Tag.연결어미, "어")
    .tag_form(Tag.보조용언, "지")
    .any()
    .msg("'쓰여지다'는 이중 피동 표현이므로 'merge((\"쓰이\", \"동사\"), ({dform[3]}, {dtag[3]}))'batchim(\"으로\", \"로\") 쓸 것을 권장합니다.")
    .build(),
    
    *rule()
    .tag_form(Tag.동사, "적히")
    .tag_form(Tag.연결어미, "어")
    .tag_form(Tag.보조용언, "지")
    .any()
    .msg("'적혀지다'는 이중 피동 표현이므로 'merge((\"적히\", \"동사\"), ({dform[3]}, {dtag[3]}))'batchim(\"으로\", \"로\") 쓸 것을 권장합니다.")
    .build(),
    
    *rule()
    .tag_form(Tag.동사, "믿기")
    .tag_form(Tag.연결어미, "어")
    .tag_form(Tag.보조용언, "지")
    .any()
    .msg("'믿겨지다'는 이중 피동 표현이므로 'merge((\"믿\", \"동사\"), (\"어\", \"연결어미\"), (\"지\", \"연결어미\"), ({dform[3]}, {dtag[3]}))'batchim(\"으로\", \"로\") 쓸 것을 권장합니다.")
    .build(),
    
    *rule()
    .tag_form(Tag.동사, "짜이")
    .tag_form(Tag.연결어미, "어")
    .tag_form(Tag.보조용언, "지")
    .any()
    .msg("'짜여지다'는 이중 피동 표현이므로 'merge((\"짜이\", \"동사\"), ({dform[3]}, {dtag[3]}))'batchim(\"으로\", \"로\") 쓸 것을 권장합니다.")
    .build(),
    
    *rule()
    .tag_form(Tag.동사, "설레이")
    .any()
    .msg("'설레이다'는 이중 피동 표현이므로 'merge((\"설레\", \"동사\"), ({dform[1]}, {dtag[1]}))'batchim(\"으로\", \"로\") 쓸 것을 권장합니다.")
    .build(),
    
    *rule()
    .tag_form(Tag.동사, "덮이")
    .tag_form(Tag.연결어미, "어")
    .tag_form(Tag.보조용언, "지")
    .any()
    .msg("'덮여지다'는 이중 피동 표현이므로 'merge((\"덮이\", \"동사\"), ({dform[3]}, {dtag[3]}))'batchim(\"으로\", \"로\") 쓸 것을 권장합니다.")
    .build(),
    
    *rule()
    .tag_form(Tag.동사, "씌이")
    .any()
    .msg("'씌이다'는 이중 피동 표현이므로 'merge((\"씌\", \"동사\"), ({dform[1]}, {dtag[1]}))'batchim(\"으로\", \"로\") 쓸 것을 권장합니다.")
    .build(),

    *rule()
    .tag_form(Tag.일반명사, "안주")
    .tag_form(Tag.의존명사, "거리")
    .if_not_spaced()
    .msg("'술과 함께 먹는 먹을거리'의 의미인 경우, '안줏거리'로 써야 합니다.")
    .build(),

    *rule()
    .tag_form(Tag.보조용언, "마")
    .tag_form(Tag.종결어미, "렴")
    .msg("'말렴'이 올바른 표현입니다.")
    .build(),

    *rule()
    .tag_form(Tag.일반명사, "윗")
    .tag_form(Tag.일반명사, "어른")
    .msg("'웃어른'이 올바른 표현입니다.").build(),
]

_REP = [
    *rule()
    .tag_form(Tag.일반명사, "제미")
    .tag_form(Tag.동사, "있")
    .msg("'재미있다'의 오타가 아닌가요?")
    .build(),

    *rule()
    .tag_form(Tag.일반명사, "회손")
    .msg("'훼손'이 올바른 표현입니다.")
    .build(),
    
    *rule()
    .tag_form(Tag.일반명사, "승락")
    .msg("'승낙'이 올바른 표현입니다.")
    .build(),

    *rule()
    .tag_form(Tag.형용사, "째째하")
    .msg("'쩨쩨하다'가 올바른 표현입니다.")
    .build(),

    *rule()
    .tag_form(Tag.동사, "수근거리")
    .msg("'수군거리다'가 올바른 표현입니다.")
    .build(),

    *rule()
    .AND(tag(Tag.일반명사), forms({"정답", "답", "문제", "퀴즈"})).context()
    .any().opt().context()
    .any().opt().context()
    .tag_form(Tag.동사, "맞추")
    .msg("문제에 대한 정답을 지칭하는 경우, '맞히다'가 올바른 표현입니다.")
    .build(),

    *rule()
    .tag_form(Tag.대명사, "이")
    .tag_form(Tag.부사격조사, "로서")
    .msg("'이것으로'의 의미일 경우 '이로써'가 올바른 표현입니다. (예시: 이로써 회의를 마치겠습니다.)")
    .build(),

    *rule()
    .AND(tags({Tag.종결어미, Tag.연결어미}), forms({"ᆯ께", "ᆯ께요"}))
    .msg("'-ᆯ게'로 써야 합니다.")
    .build(),

    *rule()
    .tag_form(Tag.어근, "내노라")
    .msg("'내로라하다'가 올바른 표현입니다.")
    .build(),

    *rule()
    .tag_form(Tag.동사, "우겨넣")
    .msg("'욱여넣다'가 올바른 표현입니다.")
    .build(),

    *rule()
    .tag_form(Tag.대명사, "느")
    .tag_form(Tag.일반명사, "김")
    .if_not_spaced()
    .msg("'느낌'의 오타가 아닌가요?")
    .build(),

    *rule()
    .tag_form(Tag.일반부사, "되려")
    .msg("'오히려'의 의미라면 '되레'가 올바른 표현입니다. 예시: 그 사람이 되레 화를 냈다.")
    .build(),

    *rule()
    .tag_form(Tag.형용사, "옳")
    .tag_form(Tag.형용사, "바르")
    .msg("'올바르다'의 오타가 아닌가요?")
    .build(),
    
    *rule()
    .tag_form(Tag.대명사, "걔")
    .tag_form(Tag.의존명사, "중")
    .tags(TagGroup.조사)
    .msg("'개중(個中)'이 올바른 표현입니다.")
    .build(),
    
    *rule()
    .tag_form(Tag.일반명사, "자욱")
    .msg("'자국'이 올바른 표현입니다.")
    .build(),
    
    *rule()
    .tag_form(Tag.일반명사, "실")
    .tag_form(Tag.일반명사, "날")
    .tag_form(Tag.형용사, "같")
    .msg("'실날같은'의 오타가 아닌가요?")
    .build(),
    
    *rule()
    .tag_form(Tag.관형사, "의존명사")
    .msg("'며칠'이 올바른 표현입니다.")
    .build(),

    *rule()
    .tag_form(Tag.감탄사, "임마")
    .msg("'인마'가 올바른 표현입니다.")
    .build(),
    
    *rule()
    .tag_form(Tag.일반명사, "멀끄러미")
    .msg("'물끄러미'가 올바른 표현입니다.")
    .build(),
    
    *rule()
    .tag_form(Tag.동사, "뒤쳐지")
    .msg("'뒤처지다'가 올바른 표현입니다.")
    .build(),
    
    *rule()
    .tag_form(Tag.형용사규칙활용, "길다랗")
    .msg("'기다랗다'가 올바른 표현입니다.")
    .build(),
    
    *rule()
    .tag_form(Tag.일반명사, "옛")
    .tag_form(Tag.형용사파생접미사규칙활용, "스럽")
    .msg("'예스럽다'가 올바른 표현입니다.")
    .build(),
    
    *rule()
    .tag_form(Tag.일반명사, "머리")
    .tag_form(Tag.일반명사, "속")
    .msg("'머릿속'이 올바른 표현입니다.")
    .build(),
    
    *rule()
    .tag_form(Tag.일반명사, "뼈")
    .tag_form(Tag.일반명사, "속")
    .msg("'뼛속'이 올바른 표현입니다.")
    .build(),
    
    *rule()
    .form("체")
    .form("안")
    .form("되")
    .tags({Tag.연결어미, Tag.선어말어미})
    .msg("'현저히 모자라다'의 의미로는 '채'가 올바른 표현입니다.")
    .build(),
    
    *rule()
    .tag_form(Tag.일반명사, "실날")
    .tag_form(Tag.형용사, "같")
    .msg("'실낱같다'가 올바른 표현입니다.")
    .build(),
    
    *rule()
    .tag_form(Tag.동사, "짓껄이")
    .msg("'지껄이다'가 올바른 표현입니다.")
    .build(),
    
    *rule()
    .tag_form(Tag.대명사, "지")
    .tag_form(Tag.동사, "꺼리")
    .if_not_spaced()
    .msg("'지껄이다'의 오타가 아닌가요?")
    .build(),
    
    *rule()
    .tag_form(Tag.동사, "추스리")
    .msg("'추스르다'가 올바른 표현입니다.")
    .build(),
    
    *rule()
    .tag_form(Tag.관형사형전성어미, "ᆫ")
    .tag_form(Tag.의존명사, "냥")
    .msg("'~인 양'이 올바른 표현입니다.")
    .build(),

    *rule()
    .tag_form(Tag.일반명사, "액")
    .tag_form(Tag.일반명사, "채")
    .msg("'액체'의 오타가 아닌가요?")
    .build(),
    
    *rule()
    .tag_form(Tag.부사격조사, "마냥")
    .msg("'마냥'은 비표준어이므로 '처럼', '같은'을 사용할 것을 권장합니다.")
    .build(),
    
    *rule()
    .id("REP_예요")
    .AND(tags({Tag.일반명사, Tag.의존명사, Tag.고유명사, Tag.명사파생접미사, Tag.명사형전성어미}), no_batchim())
    .tag_form(Tag.긍정지정사, "이").opt()
    .tag_form(Tag.종결어미, "에요")
    .msg("'{dform[0]}예요'가 올바른 표현입니다.").build(),
    
    *rule()
    .id("REP_세다")
    .AND(tag(Tag.형용사규칙활용), forms({"하얗", "허옇"})).context()
    .tag_form(Tag.연결어미, "게").context()
    .tag_form(Tag.동사, "새")
    .msg("'희어지다'의 의미로는 '세다'가 올바른 표현입니다.").build(),
    
    *rule()
    .id("REP_냬_녜")
    .form("녜")
    .msg("'~냐고 해'의 줄임말은 '냬'가 올바른 표현입니다.").build(),
    
    *rule()
    .id("REP_쭈그리다_쭈구리다")
    .tag_form(Tag.동사, "쭈구리")
    .msg("'쭈그리다'가 올바른 표현입니다.").build(),

    *rule()
    .id("REP_명사+채")
    .tag(Tag.일반명사)
    .tag_form(Tag.명사파생접미사, "채")
    .msg("'그대로, 전부'의 의미인 경우 '{dform[0]}째'가 올바른 표현입니다.").build(),

    *rule()
    .id("REP_엇")
    .tags(TagGroup.용언)
    .tag_form(Tag.선어말어미, "엇")
    .msg('\'merge(({dform[0]}, {dtag[0]}), ("었", "선어말어미"))\'의 오타가 아닌가요?').build(),
    
    *rule()
    .id("REP_멋쩍다")
    .tag_form(Tag.동사, "멎")
    .tag_form(Tag.형용사파생접미사, "쩍").if_not_spaced()
    .msg("'멋쩍다'가 올바른 표기입니다.").build(),

    *rule()
    .id("REP_메꾸다")
    .tag_form(Tag.동사, "매꾸")
    .msg("'메꾸다'가 올바른 표현입니다.").build(),

    *rule()
    .id("REP_갖히다")
    .tag_form(Tag.동사, "갖히")
    .msg("'갇히다'가 올바른 표현입니다.").build(),
]

# ᆯ 규칙 활용 관련
_ᆯ동사들 = {"졸", "썰", "날", "빌", "불", "말", "살", "일", "팔", "깃들"}
_ᆯ형용사들 = {"거칠", "달", "녹슬", "드물"}

_MIF = [
    *rule()
    .AND(tag(Tag.동사), forms(_ᆯ동사들))
    .tag_form(Tag.선어말어미, "으시")
    .msg("동사 활용이 잘못되었습니다. 'merge(({dform[0]}, {dtag[0]}), (\"다\", \"종결어미\"))'의 활용형은 'merge(({dform[0]}, {dtag[0]}), ({dform[1]}, {dtag[1]}))'batchim(\"으로\", \"로\") 써야 합니다.")
    .build(),

    *rule()
    .AND(tag(Tag.동사), forms(_ᆯ동사들))
    .tag_form(Tag.관형사형전성어미, "은")
    .msg("동사 활용이 잘못되었습니다. 'merge(({dform[0]}, {dtag[0]}), (\"다\", \"종결어미\"))'의 활용형은 'merge(({dform[0]}, \"동사\"), (\"ᆫ\", \"관형사형전성어미\"))'batchim(\"으로\", \"로\") 써야 합니다.")
    .build(),

    *rule()
    .AND(tag(Tag.형용사), forms(_ᆯ형용사들))
    .tag_form(Tag.선어말어미, "으시")
    .any()
    .context()
    .msg("형용사 활용이 잘못되었습니다. 'merge(({dform[0]}, {dtag[0]}), (\"다\", \"종결어미\"))'의 활용형은 'merge(({dform[0]}, {dtag[0]}), ({dform[1]}, {dtag[1]}))'batchim(\"으로\", \"로\") 써야 합니다.")
    .build(),

    *rule()
    .AND(tag(Tag.동사), forms(_ᆯ동사들))
    .tag_form(Tag.연결어미, "으면")
    .msg("동사 활용이 잘못되었습니다. 'merge(({dform[0]}, {dtag[0]}), (\"다\", \"종결어미\"))'의 활용형은 'merge(({dform[0]}, {dtag[0]}), ({dform[1]}, {dtag[1]}))'batchim(\"으로\", \"로\") 써야 합니다.")
    .build(),

    *rule()
    .AND(tag(Tag.형용사), forms(_ᆯ형용사들))
    .tag_form(Tag.관형사형전성어미, "은")
    .msg("형용사 활용이 잘못되었습니다. 'merge(({dform[0]}, {dtag[0]}), (\"다\", \"종결어미\"))'의 활용형은 'merge(({dform[0]}, \"형용사\"), (\"ᆫ\", \"관형사형전성어미\"))'batchim(\"으로\", \"로\") 써야 합니다.")
    .build(),
    
    *rule()
    .AND(tag(Tag.형용사), forms(_ᆯ형용사들))
    .tag_form(Tag.연결어미, "으면")
    .msg("형용사 활용이 잘못되었습니다. 'merge(({dform[0]}, {dtag[0]}), (\"다\", \"종결어미\"))'의 활용형은 'merge(({dform[0]}, {dtag[0]}), ({dform[1]}, {dtag[1]}))'batchim(\"으로\", \"로\") 써야 합니다.")
    .build(),

    *rule()
    .tag_form(Tag.주격조사, "이")
    .tag_form(Tag.긍정지정사, "이")
    .tag_form(Tag.선어말어미, "었")
    .msg("'이었다'로 써야 합니다.")
    .build(),

    *rule()
    .tag_form(Tag.긍정지정사, "이")
    .tag_form(Tag.선어말어미, "였")
    .msg("'이었다'로 써야 합니다.")
    .build(),

    *rule()
    .tag_form(Tag.동사, "붙")
    .tag_form(Tag.연결어미, "히")
    .msg("'붙이다'가 올바른 표현입니다.")
    .build(),

    *rule()
    .tags({Tag.동사, Tag.동사규칙활용, Tag.동사불규칙활용, Tag.동사파생접미사})
    .tag_form(Tag.연결어미, "ᆯ래")
    .tag_form(Tag.보조사, "야")
    .msg("'merge(({dform[0]}, {dtag[0]}), (\"려야\", \"연결어미\"))'가 올바른 표현입니다.")
    .build(),

    # 뭘 표현하려고 했는지 모르겠음. 오탐이 너무 많아서 주석 처리
    # *rule()
    # .tag_form(Tag.형용사규칙활용, "낫")
    # .tag_form(Tag.연결어미, "어")
    # .tag_form(Tag.보조용언, "지")
    # .msg("'나아지다'의 오타가 아닌가요?")
    # .build(),

    *rule()
    .tag_form(Tag.동사, "본따")
    .tags({Tag.연결어미, Tag.관형사형전성어미, Tag.선어말어미})
    .msg('\'본뜨다\'의 활용형은 \'본merge(("뜨", "동사"), ({dform[1]}, {dtag[1]}))\'batchim("으로", "로") 써야 합니다.') # fixme - merge 메서드 오동작 중. 토크나이저 쪽 문제로 보임
    .build(),

    *rule()
    .tag_form(Tag.동사, "덮히")
    .msg("'덮이다'가 올바른 표현입니다.")
    .build(),

    *rule()
    .tag_form(Tag.동사, "돋히")
    .msg("'돋치다'가 올바른 표현입니다.")
    .build(),

    *rule()
    .form("안")
    .tag_form(Tag.일반명사, "밖")
    .if_not_spaced()
    .msg("'안팎'이 올바른 표현입니다.")
    .build(),
    
    *rule()
    .tag_form(Tag.일반명사, "꾀임")
    .msg("'꼬임' 또는 '꾐'이 올바른 표현입니다.")
    .build(),
    
    *rule()
    .tag(Tag.일반명사).context()
    .tag_form(Tag.의존명사, "년도").if_spaced()
    .msg("'연도'가 올바른 표현입니다.")
    .build(),
    
    *rule()
    .tag_form(Tag.형용사, "걸맞")
    .tag_form(Tag.관형사형전성어미, "는")
    .msg("'걸맞은'이 올바른 표현입니다.")
    .build(),
    
    *rule()
    .tag_form(Tag.종결어미, "ᆸ시요")
    .msg("'~ᆸ시오'가 올바른 표현입니다.")
    .build(),
    
    *rule()
    .OR(tag_form(Tag.연결어미, "던지"), tag_form(Tag.연결어미, "던"))
    .OR(tag_form(Tag.의존명사, "간"), tag_form(Tag.보조용언, "말"))
    .msg("'든'이 올바른 표현입니다.")
    .build(),

    *rule()
    .tag_form(Tag.일반명사, "자리")
    .tag_form(Tag.목적격조사, "를")
    .tag_form(Tag.동사, "빌")
    .msg("'자리를 빌려'가 올바른 표현입니다.")
    .build(),
    
    *rule()
    .tag_form(Tag.동사, "놀래키")
    .msg("'놀래키다'는 비표준어이므로 '놀라게 하다' 등으로 써야 합니다.")
    .build(),
    
    *rule()
    .AND(tag(Tag.일반부사), forms({"두근두근", "중얼중얼", "바들바들"}))
    .form("거리")
    .msg("첩어에는 '-거리다'가 결합할 수 없습니다. '{form[0]}대다' 등으로 수정해 주세요.")
    .build(),
    
    *rule()
    .tag_form(Tag.동사, "잠구")
    .any()
    .msg("'merge((\"잠그\", \"동사\"), ({dform[1]}, {dtag[1]}))'batchim(\"이\", \"가\") 올바른 표현입니다.")
    .build(),
    
    *rule()
    .tag_form(Tag.동사, "치루")
    .any()
    .msg("'merge((\"치르\", \"동사\"), ({dform[1]}, {dtag[1]}))'batchim(\"이\", \"가\") 올바른 표현입니다.")
    .build(),
    
    *rule()
    .tag_form(Tag.동사, "돋구")
    .msg("'안경의 도수를 높이다'가 아닌 경우에는 '돋우다'로 써야 합니다. (예시: 입맛을 돋우는 향기)")
    .build(),
    
    *rule()
    .tag_form(Tag.동사, "고")
    .form("으면")
    .msg("'고다'의 활용형은 '고면'입니다.")
    .build(),
    
    *rule()
    .tag_form(Tag.동사, "모자르")
    .any()
    .msg("'merge((\"모자라\", \"동사\"), ({dform[1]}, {dtag[1]}))'batchim(\"이\", \"가\") 올바른 표현입니다.")
    .build(),
    
    *rule()
    .tag_form(Tag.동사, "널부러지")
    .msg("'널브러지다'가 올바른 표현입니다.")
    .build(),
    
    *rule()
    .tag_form(Tag.동사불규칙활용, "내딛")
    .any()
    .msg("'내디뎌', '내디뎠', '내디딜'이 올바른 표현입니다.")
    .build(),
    
    *rule()
    .tag_form(Tag.동사, "움추리")
    .msg("'움츠리다'가 올바른 표현입니다.")
    .build(),
    
    *rule()
    .tag_form(Tag.동사, "짚히")
    .msg("'짚이다'가 올바른 표현입니다.")
    .build(),
    
    *rule()
    .tag_form(Tag.동사, "붙히")
    .msg("'붙이다'가 올바른 표현입니다.")
    .build(),
    
    *rule()
    .tag_form(Tag.동사, "맞")
    .tag_form(Tag.동사, "치")
    .tag_form(Tag.연결어미, "어")
    .msg("'맞춰' 혹은 '맞혀'의 오기가 아닌지요?")
    .build(),
    
    *rule()
    .AND(tag(Tag.동사), forms({"얽히고섥히", "얼키고설키", "얽키고섥히", "얽히고섥이"}))
    .msg("'얽히고설키다'가 올바른 표현입니다.")
    .build(),
    
    *rule()
    .tag_form(Tag.동사불규칙활용, "줏")
    .msg("'주워', '주운'이 올바른 표현입니다.")
    .build(),
    
    *rule()
    .tag_form(Tag.일반명사, "넓직")
    .msg("'널찍하다'가 올바른 표현입니다.")
    .build(),

    *rule()
    .tag_form(Tag.형용사규칙활용, "넓다랗")
    .msg("'널따랗다'가 올바른 표현입니다.")
    .build(),

    *rule()
    .tag_form(Tag.일반명사, "넓직")
    .msg("'널찍하다'가 올바른 표현입니다.")
    .build(),
    
    *rule()
    .tag_form(Tag.동사, "가르키")
    .msg("'가르쳐' 혹은 '가리켜'가 올바른 표현입니다.")
    .build(),
    
    *rule()
    .tag_form(Tag.동사, "꺼매지")
    .msg("'까맣게 되다'는 '거메지다/까매지다'입니다.")
    .build(),
    
    *rule()
    .tag_form(Tag.동사, "쓰")
    .tag_form(Tag.연결어미, "어")
    .tag_form(Tag.보조용언, "있")
    .msg("'쓰여 있다'가 올바른 표현입니다.")
    .build(),
    
    *rule()
    .tag_form(Tag.일반명사, "죄")
    .tag_form(Tag.일반명사, "값")
    .if_not_spaced()
    .msg("'죗값'이 올바른 표현입니다.")
    .build(),
    
    *rule()
    .tag_form(Tag.일반명사, "홧병")
    .msg("'화병'이 올바른 표현입니다.")
    .build(),
    
    *rule()
    .tag_form(Tag.동사, "매마르")
    .msg("'메마르다'의 오타가 아닌가요?")
    .build(),

    *rule()
    .tag_form(Tag.관형사, "몇")
    .tag_form(Tag.의존명사, "일")
    .msg("'며칠'이 올바른 표현입니다.")
    .build(),

    # *rule()
    # .tag_form(Tag.동사, "날으")
    # .msg("'날다'는 '나셨다', '날면'으로 써야 합니다.")
    # .build(),
    
    *rule()
    .tags({Tag.형용사, Tag.형용사불규칙활용})
    .tag_form(Tag.연결어미, "지")
    .tag_form(Tag.보조용언, "않")
    .form("는")
    .msg("'merge(({dform[0]}, {dtag[0]}), (\"지\", \"연결어미\")) 않은'이 올바른 표현입니다.").build(),
    
    *rule()
    .any()
    .tag_form(Tag.연결어미, "다")
    .tag_form(Tag.보조용언, "싶")
    .tag_form(Tag.연결어미, "이")
    .msg("'merge(({dform[0]}, {dtag[0]}), (\"다\", \"연결어미\"))시피'가 올바른 표현입니다.").build(),

    *rule()
    .tag_form(Tag.선어말어미, "었").context()
    .tag_form(Tag.호격조사, "아")
    .msg("'어'의 오타가 아닌가요?").build(),

    *rule()
    .id("MIF_붓다_부은")
    .tag_form(Tag.동사규칙활용, "붓")
    .tag_form(Tag.관형사형전성어미, "운")
    .msg("'부은'이 올바른 표현입니다.").build(),

    *rule()
    .id("MIF_붓다_부으")
    .tag_form(Tag.동사규칙활용, "붓")
    .tag_form(Tag.연결어미, "우")
    .any().context()
    .msg("'부으'가 올바른 표현입니다.").build(),

    *rule()
    .id("MIF_동사_는구나")
    .AND(tags({Tag.동사, Tag.동사규칙활용, Tag.동사불규칙활용}), forms({"모르", "모자라", "좋아하", "닫"}))
    .tag_form(Tag.종결어미, "구나")
    .msg('동사에는 \'는구나\'가 결합하므로, \'merge(({dform[0]}, {dtag[0]}), ("는구나", "종결어미"))\'로 써야 합니다.').build(),
    
    *rule()
    .id("MIF_동사_는군")
    .AND(tags({Tag.동사, Tag.동사규칙활용, Tag.동사불규칙활용}), forms({"모르", "모자라", "좋아하", "닫"}))
    .tag_form(Tag.종결어미, "군")
    .msg('동사에는 \'는군\'이 결합하므로, \'merge(({dform[0]}, {dtag[0]}), ("는군", "종결어미"))\'으로 써야 합니다.').build(),

    *rule()
    .id("MIF_돕다")
    .tag_form(Tag.동사, "도우")
    .any()
    .msg('\'돕다\'의 활용형은 \'merge(("돕", "동사규칙활용"), ({dform[1]}, {dtag[1]}))\'batchim("으로", "로") 사용해야 합니다.').build(),
    
    *rule()
    .id("MIF_말이야")
    .tag_form(Tag.보조용언, "말")
    .tag_form(Tag.연결어미, "야").if_not_spaced()
    .msg("'말이야'를 '말야'로 줄여 쓸 수 없습니다.").build(),
    
    *rule()
    .id("MIF_려면")
    .tags({Tag.동사, Tag.동사규칙활용, Tag.동사불규칙활용, Tag.동사파생접미사})
    .tag_form(Tag.연결어미, "ᆯ려면")
    .msg('\'merge(({dform[0]}, {dtag[0]}), ("려면", "연결어미"))\'이 올바른 표현입니다.').build(),
    
    *rule()
    .id("MIF_만들려고")
    .tag_form(Tag.동사, "만드")
    .AND(tag(Tag.연결어미), forms({"려고", "려면"}))
    .msg("'만들{form[1]}'batchim(\"이\", \"가\") 올바른 표현입니다.").build(),

    *rule()
    .id("MIF_게끔")
    .tag_form(Tag.연결어미, "겠끔")
    .msg("'~게끔'이 올바른 표현입니다.").build(),

    *rule()
    .id("MIF_만듦")
    .tag_form(Tag.동사, "만들")
    .tag_form(Tag.관형사형전성어미, "ᆯ")
    .tag_form(Tag.종결어미, "음")
    .msg("'만들다'의 명사형은 '만듦'이 올바른 표기입니다.").build(),
]

JOSA_TARGETS = {Tag.일반명사, Tag.고유명사}

_JOSA = [
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

    *rule()
    .id("JOSA_은")
    .AND(tags(JOSA_TARGETS), no_batchim())
    .tag_form(Tag.보조사, "은")
    .msg('받침 없는 명사에는 \'는\'을 사용해야 합니다. \'merge(({dform[0]}, {dtag[0]}), ("는", "보조사"))\'의 오타가 아닌가요?').build(),

    *rule()
    .id("JOSA_는")
    .AND(tags(JOSA_TARGETS), any_batchim())
    .tag_form(Tag.보조사, "는")
    .msg('받침 있는 명사에는 \'은\'을 사용해야 합니다. \'merge(({dform[0]}, {dtag[0]}), ("은", "보조사"))\'의 오타가 아닌가요?').build(),

    *rule()
    .id("JOSA_이")
    .AND(tags(JOSA_TARGETS), no_batchim())
    .tag_form(Tag.주격조사, "이")
    .msg('받침 없는 명사에는 \'가\'를 사용해야 합니다. \'merge(({dform[0]}, {dtag[0]}), ("이", "주격조사"))\'의 오타가 아닌가요?').build(),

    *rule()
    .id("JOSA_가")
    .AND(tags(JOSA_TARGETS), any_batchim())
    .tag_form(Tag.주격조사, "가")
    .msg('받침 있는 명사에는 \'이\'를 사용해야 합니다. \'merge(({dform[0]}, {dtag[0]}), ("이", "주격조사"))\'의 오타가 아닌가요?').build(),

    *rule()
    .id("JOSA_과")
    .AND(tags(JOSA_TARGETS), no_batchim())
    .tag_form(Tag.접속조사, "과")
    .msg('받침 없는 명사에는 \'와\'를 사용해야 합니다. \'merge(({dform[0]}, {dtag[0]}), ("이", "접속조사"))\'의 오타가 아닌가요?').build(),

    *rule()
    .id("JOSA_와")
    .AND(tags(JOSA_TARGETS), any_batchim())
    .tag_form(Tag.접속조사, "와")
    .msg('받침 있는 명사에는 \'과\'를 사용해야 합니다. \'merge(({dform[0]}, {dtag[0]}), ("과", "접속조사"))\'의 오타가 아닌가요?').build(),

    *rule()
    .id("JOSA_과와_중복")
    .tag_form(Tag.부사격조사, "과")
    .tag_form(Tag.부사격조사, "와")
    .msg("조사가 중복으로 사용된 것 같습니다.").build(),

    *rule()
    .id("JOSA_와과_중복")
    .tag_form(Tag.부사격조사, "와")
    .tag_form(Tag.부사격조사, "과")
    .msg("조사가 중복으로 사용된 것 같습니다.").build(),
]

_SHIFT_MISS = [
    *rule()
    .tag_form(Tag.동사, "끄")
    .if_not_spaced()
    .tag_form(Tag.선어말어미, "었")
    .msg("'껏'의 오타가 아닌가요?")
    .build(),
    
    *rule()
    .tag_form(Tag.선어말어미, "겟")
    .msg("'겠'의 오타가 아닌가요?")
    .build(),
    
    *rule()
    .tag_form(Tag.동사, "하")
    .tag_form(Tag.선어말어미, "엇")
    .msg("'했'의 오타가 아닌가요?")
    .build(),
]

_DEPENDS_ON_DICTIONARY = [
    *rule()
    .tag_form(Tag.동사, "건내")
    .msg("'건네다'의 오타가 아닌가요?")
    .build(),
]

_NOT_CERTAINS = [
    
]

_LOANWORDS = [
    *rule()
    .id("LOANWORD_브러쉬")
    .form("브러쉬")
    .msg("'브러시'가 올바른 표기입니다.").build(),
    
    *rule()
    .id("LOANWORD_드롭")
    .form("드랍")
    .msg("'드롭(drop)'이 올바른 표기입니다.").build(),
    
    *rule()
    .id("LOANWORD_배턴")
    .forms({"배톤", "배턴", "바톤"})
    .msg("'배턴' 또는 '바통'이 올바른 표기입니다.").build(),
    
    *rule()
    .id("LOANWORD_튀르키예")
    .tag_form(Tag.고유명사, "터키")
    .msg("나라 이름인 경우, '튀르키예'가 올바른 표기입니다.").build(),
    
    *rule()
    .id("LOANWORD_타월")
    .tag_form(Tag.일반명사, "타올")
    .msg("'타월'이 올바른 표기입니다.").build(),
    
    *rule()
    .id("LOANWORD_수프")
    .tag_form(Tag.일반명사, "스프")
    .msg("'수프(soup)'가 올바른 표기입니다.").build(),
    
    *rule()
    .id("LOANWORD_레포트")
    .tag_form(Tag.일반명사, "레포트")
    .msg("'리포트'가 올바른 표기입니다.").build(),

    *rule()
    .id("LOANWORD_프러포즈")
    .tag_form(Tag.일반명사, "프로포즈")
    .msg("'프러포즈'가 올바른 표기입니다.").build(),

    *rule()
    .id("LOANWORD_칼럼")
    .tag_form(Tag.일반명사, "컬럼")
    .msg("'칼럼'이 올바른 표기입니다.").build(),
]

def rule() -> RuleBuilder:
    return RuleBuilder(SpellErrorType.NEED_ML_JUDGE)

_NEED_ML_JUDGE = [
    *rule()
    .id("형상_현상_오타")
    .tag_form(Tag.일반명사, "형상") # '현상'
    .msg("'현상'의 오타가 아닌가요?")
    .build(),

    *rule()
    .id("뺐다_뺏다_오타")
    .tag_form(Tag.동사, "빼")
    .tag_form(Tag.선어말어미, "었")
    .msg("'뺏다'의 오타가 아닌가요?")
    .build(),

    *rule()
    .id("띄다_띠다_오타")
    .tag_form(Tag.동사, "띄")
    .msg("'띠다'의 오기가 아닌가요?")
    .build(),
    
    *rule()
    .id("붓기_부기_오타")
    .tag_form(Tag.동사규칙활용, "붓")
    .tag_form(Tag.명사형전성어미, "기")
    .msg("'부은 정도'는 '부기'가 올바른 표현입니다.")
    .build(),
    
    *rule()
    .id("던가_든가_오타")
    .tag(Tag.긍정지정사)
    .tag_form(Tag.종결어미, "라던가")
    .msg("나열할 때는 '라든가'가 올바른 표현입니다.")
    .build(),
    
    *rule()
    .id("아니오_아니요_오타")
    .form("아니")
    .form("오")
    .msg("존대의 의미라면 '아니요'입니다. '아니오'는 하게체의 말투입니다. ('아니라오' 같은 것)")
    .build(),
    
    *rule()
    .id("회수_횟수_오타")
    .form("회수")
    .msg("'횟수(回数)'의 오타가 아닌가요?")
    .build(),

    *rule()
    .id("캐롤_캐럴_오타")
    .tag_form(Tag.고유명사, "캐롤")
    .msg("'캐럴'로 써야 합니다.")
    .build(),
    
    *rule()
    .id("들르다_들리다_오타")
    .tag_form(Tag.동사, "들리")
    .msg("'지나가는 길에 방문하다'의 의미로는 '들르다'가 올바른 표현입니다.").build(),

    *rule()
    .id("쥐여주다_오타")
    .tag_form(Tag.동사, "쥐")
    .tag_form(Tag.연결어미, "어")
    .tag_form(Tag.보조용언, "주")
    .msg("'쥐게 하다'의 의미로는 '쥐여 주다'가 올바른 표현입니다.").build(),
]

SPELL_MISS_ERRORS = [
    *_CERTAINS,
    *_NOT_CERTAINS,
    *_DEPENDS_ON_DICTIONARY,
    *_OM,
    *_ADD,
    *_REP,
    *_MIF,
    *_JOSA,
    *_SHIFT_MISS,
    *_LOANWORDS
]