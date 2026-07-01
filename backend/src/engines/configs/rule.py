from src.engines.configs.rule_builder import *
from src.models.interface import Tag, TagGroup, SpellErrorType
from src.engines.configs import rule_meaning, rule_spacing, rule_specific, rule_spelling, rule_warning, rule_complex, rule_model
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
    *rule().id("JOSA_으로")
    .AND(tags(JOSA_TARGETS), OR(no_batchim(), batchim("ᆯ")))
    .tag_form(Tag.부사격조사, "으로")
    .msg('받침이 없거나 ㄹ로 끝나는 명사에는 \'로\'를 사용해야 합니다. \'merge(({dform[0]}, {dtag[0]}), ("로", "부사격조사"))\'의 오타가 아닌가요?').build(),
    
    *rule().id("JOSA_으로_괄호")
    .AND(tags(JOSA_TARGETS), OR(no_batchim(), batchim("ᆯ")))
    .tag_form(Tag.여는부호, "(")
    .any()
    .any().opt()
    .tag_form(Tag.닫는부호, ")")
    .tag_form(Tag.부사격조사, "으로")
    .msg('받침이 없거나 ㄹ로 끝나는 명사에는 \'로\'를 사용해야 합니다. \'merge(({dform[0]}, {dtag[0]}), ("로", "부사격조사"))\'의 오타가 아닌가요?').build(),

    *rule().id("JOSA_로")
    .AND(tags(JOSA_TARGETS), AND(any_batchim(), NOT(batchim("ᆯ"))))
    .tag_form(Tag.부사격조사, "로")
    .msg('ㄹ이 아닌 받침으로 끝나는 명사에는 \'으로\'를 사용해야 합니다. \'merge(({dform[0]}, {dtag[0]}), ("으로", "부사격조사"))\'의 오타가 아닌가요?').build(),
    
    *rule().id("JOSA_로")
    .AND(tags(JOSA_TARGETS), AND(any_batchim(), NOT(batchim("ᆯ"))))
    .tag_form(Tag.여는부호, "(")
    .any()
    .any().opt()
    .tag_form(Tag.닫는부호, ")")
    .tag_form(Tag.부사격조사, "로")
    .msg('ㄹ이 아닌 받침으로 끝나는 명사에는 \'으로\'를 사용해야 합니다. \'merge(({dform[0]}, {dtag[0]}), ("으로", "부사격조사"))\'의 오타가 아닌가요?').build(),

    *rule().id("JOSA_을")
    .AND(tags(JOSA_TARGETS), no_batchim())
    .tag_form(Tag.목적격조사, "을")
    .msg('받침 없는 명사에는 \'를\'을 사용해야 합니다. \'merge(({dform[0]}, {dtag[0]}), ("를", "목적격조사"))\'의 오타가 아닌가요?').build(),

    *rule().id("JOSA_을_괄호")
    .AND(tags(JOSA_TARGETS), no_batchim())
    .tag_form(Tag.여는부호, "(")
    .any()
    .any().opt()
    .tag_form(Tag.닫는부호, ")")
    .tag_form(Tag.목적격조사, "을")
    .msg('받침 없는 명사에는 \'를\'을 사용해야 합니다. \'merge(({dform[0]}, {dtag[0]}), ("를", "목적격조사"))\'의 오타가 아닌가요?').build(),

    *rule().id("JOSA_를")
    .AND(tags(JOSA_TARGETS), any_batchim())
    .tag_form(Tag.목적격조사, "를")
    .msg('받침 있는 명사에는 \'을\'을 사용해야 합니다. \'merge(({dform[0]}, {dtag[0]}), ("을", "목적격조사"))\'의 오타가 아닌가요?').build(),

    *rule().id("JOSA_를_괄호")
    .AND(tags(JOSA_TARGETS), any_batchim())
    .tag_form(Tag.여는부호, "(")
    .any()
    .any().opt()
    .tag_form(Tag.닫는부호, ")")
    .tag_form(Tag.목적격조사, "를")
    .msg('받침 있는 명사에는 \'을\'을 사용해야 합니다. \'merge(({dform[0]}, {dtag[0]}), ("을", "목적격조사"))\'의 오타가 아닌가요?').build(),

    *rule().id("JOSA_은_1")
    .AND(tags(JOSA_TARGETS), no_batchim())
    .tag_form(Tag.보조사, "은")
    .msg('받침 없는 명사에는 \'는\'을 사용해야 합니다. \'merge(({dform[0]}, {dtag[0]}), ("는", "보조사"))\'의 오타가 아닌가요?').build(),
    
    *rule().id("JOSA_은_2")
    .tag_form(Tag.명사파생접미사, "들").context()
    .tag_form(Tag.관형사형전성어미, "는")
    .msg("'은'의 오타가 아닌가요?").build(),
    
    *rule().id("JOSA_은_괄호")
    .AND(tags(JOSA_TARGETS), no_batchim())
    .tag_form(Tag.여는부호, "(")
    .any()
    .any().opt()
    .tag_form(Tag.닫는부호, ")")
    .tag_form(Tag.보조사, "은")
    .msg('받침 없는 명사에는 \'는\'을 사용해야 합니다. \'merge(({dform[0]}, {dtag[0]}), ("는", "보조사"))\'의 오타가 아닌가요?').build(),

    *rule().id("JOSA_는")
    .AND(tags(JOSA_TARGETS), any_batchim())
    .tag_form(Tag.보조사, "는")
    .msg('받침 있는 명사에는 \'은\'을 사용해야 합니다. \'merge(({dform[0]}, {dtag[0]}), ("은", "보조사"))\'의 오타가 아닌가요?').build(),
    
    *rule().id("JOSA_는_괄호")
    .AND(tags(JOSA_TARGETS), any_batchim())
    .tag_form(Tag.여는부호, "(")
    .any()
    .any().opt()
    .tag_form(Tag.닫는부호, ")")
    .tag_form(Tag.보조사, "는")
    .msg('받침 있는 명사에는 \'은\'을 사용해야 합니다. \'merge(({dform[0]}, {dtag[0]}), ("은", "보조사"))\'의 오타가 아닌가요?').build(),

    *rule().id("JOSA_이")
    .AND(tags(JOSA_TARGETS), no_batchim())
    .tag_form(Tag.주격조사, "이")
    .msg('받침 없는 명사에는 \'가\'를 사용해야 합니다. \'merge(({dform[0]}, {dtag[0]}), ("이", "주격조사"))\'의 오타가 아닌가요?').build(),
    
    *rule().id("JOSA_이_괄호")
    .AND(tags(JOSA_TARGETS), no_batchim())
    .tag_form(Tag.여는부호, "(")
    .any()
    .any().opt()
    .tag_form(Tag.닫는부호, ")")
    .tag_form(Tag.주격조사, "이")
    .msg('받침 없는 명사에는 \'가\'를 사용해야 합니다. \'merge(({dform[0]}, {dtag[0]}), ("이", "주격조사"))\'의 오타가 아닌가요?').build(),

    *rule().id("JOSA_가")
    .AND(tags(JOSA_TARGETS), any_batchim())
    .tag_form(Tag.주격조사, "가")
    .msg('받침 있는 명사에는 \'이\'를 사용해야 합니다. \'merge(({dform[0]}, {dtag[0]}), ("이", "주격조사"))\'의 오타가 아닌가요?').build(),
    
    *rule().id("JOSA_가_괄호")
    .AND(tags(JOSA_TARGETS), any_batchim())
    .tag_form(Tag.여는부호, "(")
    .any()
    .any().opt()
    .tag_form(Tag.닫는부호, ")")
    .tag_form(Tag.주격조사, "가")
    .msg('받침 있는 명사에는 \'이\'를 사용해야 합니다. \'merge(({dform[0]}, {dtag[0]}), ("이", "주격조사"))\'의 오타가 아닌가요?').build(),

    *rule().id("JOSA_과")
    .AND(tags(JOSA_TARGETS), no_batchim())
    .tag_form(Tag.접속조사, "과")
    .msg('받침 없는 명사에는 \'와\'를 사용해야 합니다. \'merge(({dform[0]}, {dtag[0]}), ("이", "접속조사"))\'의 오타가 아닌가요?').build(),
    
    *rule().id("JOSA_과_괄호")
    .AND(tags(JOSA_TARGETS), no_batchim())
    .tag_form(Tag.여는부호, "(")
    .any()
    .any().opt()
    .tag_form(Tag.닫는부호, ")")
    .tag_form(Tag.접속조사, "과")
    .msg('받침 없는 명사에는 \'와\'를 사용해야 합니다. \'merge(({dform[0]}, {dtag[0]}), ("이", "접속조사"))\'의 오타가 아닌가요?').build(),

    *rule().id("JOSA_와")
    .AND(tags(JOSA_TARGETS), any_batchim())
    .tag_form(Tag.접속조사, "와")
    .msg('받침 있는 명사에는 \'과\'를 사용해야 합니다. \'merge(({dform[0]}, {dtag[0]}), ("과", "접속조사"))\'의 오타가 아닌가요?').build(),
    
    *rule().id("JOSA_와_괄호")
    .AND(tags(JOSA_TARGETS), any_batchim())
    .tag_form(Tag.여는부호, "(")
    .any()
    .any().opt()
    .tag_form(Tag.닫는부호, ")")
    .tag_form(Tag.접속조사, "와")
    .msg('받침 있는 명사에는 \'과\'를 사용해야 합니다. \'merge(({dform[0]}, {dtag[0]}), ("과", "접속조사"))\'의 오타가 아닌가요?').build(),

    *rule().id("JOSA_과와_중복")
    .tag_form(Tag.부사격조사, "과")
    .tag_form(Tag.부사격조사, "와")
    .msg("조사가 중복으로 사용된 것 같습니다.").build(),

    *rule().id("JOSA_와과_중복")
    .tag_form(Tag.부사격조사, "와")
    .tag_form(Tag.부사격조사, "과")
    .msg("조사가 중복으로 사용된 것 같습니다.").build(),
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
    # *rule_warning.WARNINGS,
 ]