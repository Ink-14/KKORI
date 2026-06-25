from src.engines.configs.rule_builder import RuleBuilder, AND, OR, NOT, tag, tags, tag_form, form, forms, lemma, batchim, longer, SpacingRule, KoSpellRules
from src.models.interface import Tag, TagGroup, SpellErrorType
from src.engines.configs.rule_constants import 보조용언_FORMS

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
    .tag_form(Tag.동사, "나").if_not_spaced()
    .msg("'파투 나다'가 올바른 표현입니다.").build(),

    *rule().id("COMPLEX_흩트리+보조용언")
    .tag_form(Tag.동사, "흐트리")
    .tag(Tag.연결어미)
    .AND(tag(Tag.보조용언), forms(보조용언_FORMS)).if_not_spaced()
    .msg('\'흩트려 merge(({dform[2]}, "보조용언"), ("다", "종결어미"))\'가 올바른 표현입니다.').build(),
]

COMPLEX_ERRORS: list[KoSpellRules] = [
    *_SPELLING_SPACING,
]