from src.engines.configs.rule_builder import RuleBuilder, AND, OR, NOT, tag, tags, tag_form, form, forms, lemma, batchim, longer, SpacingRule, KoSpellRules
from src.models.interface import Tag, TagGroup, SpellErrorType

def rule() -> RuleBuilder: # type: ignore
    return RuleBuilder(SpellErrorType.SUPPRESS_ALL)

_SPACING = [
    *rule().id("SUP_눈 깜짝할 사이")
    .tag_form(Tag.일반명사, "눈")
    .tag_form(Tag.일반부사, "깜짝")
    .tag_form(Tag.동사파생접미사, "하").if_not_spaced().build(),

    *rule().id("SUP_O형제/자매 간")
    .tags({Tag.수사, Tag.관형사})
    .forms({"형제", "자매"})
    .tag_form(Tag.의존명사, "간").if_spaced().build(),
]

SUPRESS_RULES = [
    *_SPACING,
]