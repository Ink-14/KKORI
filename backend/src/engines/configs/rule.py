from src.engines.configs.rule_builder import *
from src.models.interface import Tag, TagGroup, SpellErrorType
from src.engines.configs import rule_meaning, rule_spacing, rule_specific, rule_spelling, rule_warning, rule_complex, rule_proofread, rule_model
from src.engines.configs.rule_constants import *

# 규칙 작성 예시
def rule() -> RuleBuilder:
    return RuleBuilder(SpellErrorType.TEST)

SAMPLE = [
    *rule()
    .tags({Tag.형용사, Tag.형용사불규칙활용})
    .tag_form(Tag.연결어미, "지")
    .tag_form(Tag.보조용언, "않")
    .form("는")
    .msg("'merge(({dform[0]}, {dtag[0]}), (\"지\", \"연결어미\")) 않은'이 올바른 표현입니다.").build(),
]

TEST_SPELL_CHECK_RULES = [
    *rule().id("XSN_분_붙여쓰기")
    .AND(tag(Tag.일반명사), forms(분_MUST_ATTACHED_NOUNS))
    .tag_form(Tag.의존명사, "분").if_spaced()
    .msg("'{dform[0]}분'으로 붙여 써야 합니다.")
    .detail("이때의 '분'은 앞 말에 붙여 높임의 의미를 나타내는 접사입니다. 따라서 없어도 문장이 성립한다면 붙여 써야 하고, 없을 때 문장이 성립하지 않으면 의존명사이므로 띄어 써야 합니다.\n(접사인 경우) 남편분이 직접 와 주세요. / 남편이 직접 와 주세요.\n(의존명사인 경우) 많은 분들이 모여 주셨습니다. / 많은 들이 모여 주셨습니다.").build(),
]

ML_LABELINGS = [
]

SPELL_CHECK_RULES: list[KoSpellRules] = [
    *rule_spacing.GENERAL_SPACING_ERRORS,
    *rule_spacing.SPACING_ERRORS,
    *rule_spelling.SPELL_MISS_ERRORS,
    *rule_meaning.MEANING_CONFLICT_ERRORS,
    *rule_specific.KIWI_EXCEPTION_ERRORS,
    *rule_complex.COMPLEX_ERRORS,
    *rule_proofread.PROOFREAD_ERRORS,
    # *rule_warning.WARNINGS,
 ]