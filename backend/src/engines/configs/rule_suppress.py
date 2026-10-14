from src.engines.configs.rule_builder import RuleBuilder, AND, OR, NOT, tag, tags, tag_form, form, forms, lemma, batchim, longer, SpacingRule, KoSpellRules
from src.models.interface import Tag, TagGroup, SpellErrorType

def rule() -> RuleBuilder: # type: ignore
    return RuleBuilder(SpellErrorType.SUPPRESS)

_SPACING = [
    *rule().id("SUP_눈 깜짝할 사이")
    .tag_form(Tag.일반명사, "눈")
    .tag_form(Tag.일반부사, "깜짝")
    .tag_form(Tag.동사파생접미사, "하").if_not_spaced().build(),

    *rule().id("SUP_O형제/자매 간")
    .tags({Tag.수사, Tag.관형사})
    .forms({"형제", "자매"})
    .tag_form(Tag.의존명사, "간").if_spaced().build(),
    
    *rule().id("SUP_숨어들다") # 도저히 억제가 안 돼서 추가 규칙 등록
    .tag_form(Tag.동사, "숨").context()
    .tag_form(Tag.연결어미, "어")
    .tag_form(Tag.보조용언, "들").if_not_spaced().build(),
    
    *rule().id("SUP_따라 오다")
    .tag(Tag.목적격조사).context()
    .tag_form(Tag.동사, "따르")
    .tag_form(Tag.연결어미, "어")
    .tag_form(Tag.동사, "오").if_spaced()
    .tag_form(Tag.선어말어미, "었").context()
    .tag_form(Tag.관형사형전성어미, "던").context()
    .tag_form(Tag.일반명사, "길").context()
    .tag_form(Tag.부사격조사, "로").context()
    .tag_form(Tag.동사, "돌아가").context().build(),
]

SUPRESS_RULES = [
    *_SPACING,
]
