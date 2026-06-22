from src.engines.configs.rule_builder import RuleBuilder, AND, OR, NOT, tag, tags, tag_form, form, forms, lemma, batchim, longer, SpacingRule, KoSpellRules
from src.models.interface import Tag, TagGroup, SpellErrorType

def rule() -> RuleBuilder:
    return RuleBuilder(SpellErrorType.COMPLEX)

_SPELLING_SPACING = [
    *rule().id("complex_@@년도")
    .tag(Tag.일반명사)
    .form("년도").if_not_spaced()
    .msg("'{dform[0]} 연도'가 올바른 표현입니다.").build(),

    *rule().id("complex_안주 거리")
    .tag_form(Tag.일반명사, "안주")
    .tag_form(Tag.의존명사, "거리").if_spaced()
    .msg("'안줏거리'가 올바른 표현입니다.").build(),
]

COMPLEX_ERRORS: list[KoSpellRules] = [
    *_SPELLING_SPACING,
]