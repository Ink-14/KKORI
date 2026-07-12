from src.engines.configs.rule_builder import RuleBuilder, AND, OR, NOT, tag, tags, tag_form, form, forms, lemma, batchim, longer, SpacingRule, KoSpellRules
from src.models.interface import Tag, TagGroup, SpellErrorType

def rule() -> RuleBuilder: # type: ignore
    return RuleBuilder(SpellErrorType.PROOFREAD)

PROOFREAD_ERRORS = [
    *rule().id("PROOFREAD_~ㄹ 수")
    .AND(tag(Tag.관형사형전성어미), forms({"을", "ᆯ"})).context()
    .tag_form(Tag.의존명사, "수")
    .AND(tag(Tag.일반명사), NOT(form("밖")))
    .tag(Tag.목적격조사).context()
    .msg("'수' 뒤에 무언가 빠진 것 같습니다.").build(),
]