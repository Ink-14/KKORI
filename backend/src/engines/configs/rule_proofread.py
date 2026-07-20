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

    *rule().id("PROOFREAD_다다르다")
    .tag_form(Tag.일반명사, "최고").context()
    .tag_form(Tag.부사격조사, "에").context()
    .tag_form(Tag.동사규칙활용, "닫")
    .any()
    .msg("최고에 '다다르다', '달하다', '닿다'의 잘못이 아닌가요?").build(),

    *rule().id("PROOFREAD_하게 위해")
    .AND(tags({Tag.동사파생접미사, Tag.동사}), form("하")).context()
    .tag_form(Tag.연결어미, "게")
    .tag_form(Tag.동사, "위하").context()
    .msg("'하기 위해'가 아닌가요?").build(),
]