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

    *rule().id("COMPLEX_갖다 놓다+띄어쓰기")
    .tag_form(Tag.동사, "가")
    .tag_form(Tag.선어말어미, "었")
    .tag_form(Tag.연결어미, "다")
    .tag_form(Tag.보조용언, "놓").if_not_spaced()
    .msg("'갖다 놓다'로 써야 합니다.").build(),

    *rule().id("COMPLE_때_오타+띄어쓰기")
    .NOT(tag_form(Tag.동사, "쓰"))
    .tag_form(Tag.관형사형전성어미, "ᆯ").if_not_spaced().context()
    .form("떄")
    .msg("'merge(({dform[0]}, {dtag[0]}), (\"ᆯ\", \"관형사형전성어미\")) 때'의 오타가 아닌가요?").build(),

    *rule().id("COMPLE_쓸데_오타+띄어쓰기_1")
    .tag_form(Tag.동사, "쓰")
    .tag_form(Tag.관형사형전성어미, "ᆯ")
    .forms({"때", "떄"})
    .tag_form(Tag.형용사, "없").if_spaced()
    .msg("'쓸데없다'가 올바른 표현입니다.").build(),

    *rule().id("COMPLE_쓸데_오타+띄어쓰기_1")
    .tag_form(Tag.동사, "쓰")
    .tag_form(Tag.관형사형전성어미, "ᆯ")
    .forms({"때", "떄"})
    .tag_form(Tag.일반부사, "없이").if_spaced()
    .msg("'쓸데없이'가 올바른 표현입니다.").build(),
]

COMPLEX_ERRORS: list[KoSpellRules] = [
    *_SPELLING_SPACING,
]