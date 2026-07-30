from src.engines.configs.rule_builder import RuleBuilder, AND, OR, NOT, tag, tags, tag_form, form, forms, lemma, batchim, longer, SpacingRule, KoSpellRules
from src.models.interface import Tag, TagGroup, SpellErrorType

def rule() -> RuleBuilder:
    return RuleBuilder(SpellErrorType.PROOFREAD)

PROOFREAD_ERRORS = [
    *rule().id("PROOFREAD_~ㄹ 수")
    .AND(tag(Tag.관형사형전성어미), forms({"을", "ᆯ"})).context()
    .tag_form(Tag.의존명사, "수")
    .AND(tag(Tag.일반명사), NOT(form("밖")))
    .tag(Tag.목적격조사).context()
    .msg("'수' 뒤에 무언가 빠진 것 같습니다.").build(),

    *rule().id("PRFR_다다르다")
    .tag_form(Tag.일반명사, "최고").context()
    .tag_form(Tag.부사격조사, "에").context()
    .tag_form(Tag.동사규칙활용, "닫")
    .any()
    .msg("최고에 '다다르다', '달하다', '닿다'의 잘못이 아닌가요?").build(),

    *rule().id("PRFR_하게 위해")
    .AND(tags({Tag.동사파생접미사, Tag.동사}), form("하")).context()
    .tag_form(Tag.연결어미, "게")
    .tag_form(Tag.동사, "위하").context()
    .msg("'하기 위해'가 아닌가요?").build(),
    
    *rule().id("PRFR_왔는 반면")
    .tags(TagGroup.용언)
    .tag_form(Tag.선어말어미, "었")
    .tag_form(Tag.관형사형전성어미, "는")
    .tag_form(Tag.일반명사, "반면")
    .msg('\'merge(({dform[0]}, {dtag[0]}), ("ᆫ", "관형사형전성어미")) 반면\'의 잘못이 아닌가요?').build(),
    
    *rule().id("PRFR_구나리고")
    .tag_form(Tag.종결어미, "구나")
    .tag_form(Tag.인용격조사, "고")
    .msg("'구나라고'의 잘못이 아닌가요?").build(),

    *rule().id("PRFR_~을 있기에")
    .tags(TagGroup.체언)
    .tag(Tag.목적격조사)
    .tag_form(Tag.동사, "있").context()
    .tag_form(Tag.연결어미, "기에").context()
    .msg("'{dform[0]}batchim(\"이\", \"가\") 있기에'의 잘못이 아닌가요?").build(),

    *rule().id("PRFR_~에게 대한")
    .tag_form(Tag.부사격조사, "에게")
    .tag_form(Tag.동사, "대하").context()
    .tag_form(Tag.관형사형전성어미, "ᆫ").context()
    .msg("'~에 대한'의 잘못이 아닌가요?").build(),

    *rule().id("PRFR_~을 바뀐 걸")
    .tag(Tag.일반명사)
    .tag(Tag.목적격조사)
    .tag_form(Tag.동사, "바뀌")
    .tag_form(Tag.관형사형전성어미, "ᆫ")
    .tag_form(Tag.의존명사, "거").context()
    .tag_form(Tag.목적격조사, "ᆯ").context()
    .msg("'{dform[0]}batchim(\"이\", \"가\") 바뀐' 또는 '{dform[0]}batchim(\"을\", \"를\") 바꾼'의 잘못이 아닌가요?").build(),

    *rule().id("PRFR_이루어 있다")
    .tag_form(Tag.동사, "이루")
    .tag_form(Tag.연결어미, "어")
    .tag_form(Tag.보조용언, "있")
    .msg("'이루어져 있다'의 잘못이 아닌가요?").build(),

    *rule().id("PRFR_말았는 것")
    .tag_form(Tag.보조용언, "말")
    .tag_form(Tag.선어말어미, "었")
    .tag_form(Tag.관형사형전성어미, "는")
    .tag_form(Tag.의존명사, "것").context()
    .msg("'만'의 잘못이 아닌가요?").build(),
]