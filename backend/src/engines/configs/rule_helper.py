from src.engines.configs.rule_builder import *
from src.engines.configs.rule_constants import 모음연결어미_FORMS, 모음선어말어미_FORMS, 모음관형사형전성어미_FORMS
from src.models.interface import Tag, TagGroup, SpellErrorType

def word_3(word1: str, tag1: Tag, word2: str, tag2: Tag, word3: str, tag3: Tag, spacing_rule: SpacingRule, message: str):
    rule = RuleBuilder(SpellErrorType.SPACING).tag_form(tag1, word1).tag_form(tag2, word2).tag_form(tag3, word3)

    if spacing_rule == SpacingRule.SPACED:
        return rule.if_not_spaced().msg(f"'{message}'batchim(\"으로\",\"로\") 띄어 써야 합니다.").build()
    elif spacing_rule == SpacingRule.ATTACHED:
        return rule.if_spaced().msg(f"'{message}'batchim(\"으로\",\"로\") 붙여 써야 합니다.").build()
    elif spacing_rule == SpacingRule.ANY:
        raise ValueError("'Any' spacing rule is not allowed in word_3.")

def NNG_and_NNG(nng1: str, nng2: str, spacing_rule: SpacingRule, message = None) -> list[KoSpellRules]:
    rule = RuleBuilder(SpellErrorType.SPACING).id(f"NNG_and_NNG_{nng1}_{nng2}").tag_form(Tag.일반명사, nng1).tag_form(Tag.일반명사, nng2)
    
    if spacing_rule == SpacingRule.SPACED:
        rule.if_not_spaced()
        if message is None:
            message = "'{form[0]} {form[1]}'batchim(\"으로\",\"로\") 띄어 써야 합니다."
    elif spacing_rule == SpacingRule.ATTACHED:
        rule.if_spaced()
        if message is None:
            message = "'{form[0]}{form[1]}'batchim(\"으로\",\"로\") 붙여 써야 합니다."
    elif spacing_rule == SpacingRule.ANY:
        if message is None:
            raise ValueError("you must set error message to function 'NNG_and_NNG' if spacing rule is SpacingRule.ANY.")
        
    return rule.msg(message).build()
    
def NNG_and_some(nng: str, some: str, tag: str, spacing_rule: SpacingRule, message = None) -> list[KoSpellRules]:
    rule = RuleBuilder(SpellErrorType.SPACING).id(f"NNG_SOME_{nng}{some}다").tag_form(Tag.일반명사, nng).tag_form(Tag[tag], some)
    
    message = f"merge((\"{some}\", \"{tag}\"), (\"다\", \"연결어미\"))"
    if spacing_rule == SpacingRule.SPACED:
        message = "{form[0]} " + message
        return rule.if_not_spaced().msg(f"'{message}'로 띄어 써야 합니다.").build()
    elif spacing_rule == SpacingRule.ATTACHED:
        message = "{form[0]}" + message
        return rule.if_spaced().msg(f"'{message}'로 붙여 써야 합니다.").build()
    elif spacing_rule == SpacingRule.ANY:
        if message is None:
            raise ValueError("you must set error message to function 'NNG_and_some' if spacing rule is SpacingRule.ANY.")
        return rule.msg(message).build()
    
def VV_EC_VV(vv1: tuple[str, str], ec: str, vv2: tuple[str, str], spacing_rule: SpacingRule, message: None | str = None, detail: None | str = None) -> list[KoSpellRules]:
    vv1_form, vv1_tag = vv1
    vv2_form, vv2_tag = vv2
    rule = RuleBuilder(SpellErrorType.SPACING).id(f"VV_EC_VV_{vv1_form}_{ec}_{vv2_form}").tag_form(Tag[vv1_tag], vv1_form).tag_form(Tag.연결어미, ec).tag_form(Tag[vv2_tag], vv2_form)

    message1 = f"merge((\"{vv1_form}\", \"{vv1_tag}\"), (\"{ec}\", \"연결어미\"))"
    message2 = f"merge((\"{vv2_form}\", \"{vv2_tag}\"), (\"다\", \"연결어미\"))"
    
    if spacing_rule == SpacingRule.SPACED:
        rule.if_not_spaced()
        if message is None:
            rule.msg(f"'{message1} {message2}'로 띄어 써야 합니다.")
        else:
            rule.msg(message)
    elif spacing_rule == SpacingRule.ATTACHED:
        rule.if_spaced()
        if message is None:
            rule.msg(f"'{message1}{message2}'로 붙여 써야 합니다.")
        else:
            rule.msg(message)
    elif spacing_rule == SpacingRule.ANY:
        if message is None:
            raise ValueError("you must set error message to function 'VV_EC_VV' if spacing rule is SpacingRule.ANY.")
        rule.msg(message)

    if detail is not None:
        rule.detail(detail)

    return rule.build()

def abbr_vowel_ending_connectives(abbr: str, abbr_tag: Tag, origin: str, origin_tag: Tag) -> list[KoSpellRules]:
    """
    준말에 모음 어미가 결합한 경우를 감지하는 규칙을 만들어 주는 헬퍼입니다.
    """
    detail = f"준말에는 모음 어미가 결합할 수 없습니다. '{abbr}다'는 '{origin}다'의 준말로서, 모음 어미가 결합할 경우 원래 형태인 '{origin}다'를 사용해야 합니다."
    
    def make_base():
        return RuleBuilder(SpellErrorType.SPELLING).id(f"abbr_vowel_{abbr}다").tag_form(abbr_tag, abbr).msg(f'\'merge(("{origin}", "{origin_tag.name}"),' + '({dform[1]}, {dtag[1]}))\'batchim("이", "가") 올바른 표현입니다.').detail(detail)
    
    rule_ec = make_base().AND(tag(Tag.연결어미), forms(모음연결어미_FORMS))
    rule_ep = make_base().AND(tag(Tag.선어말어미), forms(모음선어말어미_FORMS))
    rule_etm = make_base().AND(tag(Tag.관형사형전성어미), forms(모음관형사형전성어미_FORMS))
    
    return [*rule_ec.build(), *rule_ep.build(), *rule_etm.build()]

def 로서_combinations(jkb_target_value: str, jkb_target_tag: Tag, following_word_value: str = None, following_word_tag: Tag = None):
    """
    '로서'가 쓰여야 하는 곳에 '로써'가 쓰인 경우를 감지하는 규칙을 만들어 주는 헬퍼입니다.
    jkb_target_value, jkb_target_tag: '로서' 앞에 위치한 토큰.
    following_word_value, following_word_tag: '로서' 뒤에 위치한 토큰.
    """
    result = RuleBuilder(SpellErrorType.SPELLING).id(f"로서_combinations_{jkb_target_value}_로서_{following_word_value}").tag_form(jkb_target_tag, jkb_target_value).context().tag_form(Tag.부사격조사, "로써")

    if following_word_value is not None:
        result.tag_form(following_word_tag, following_word_value).context()

    return result.msg("'로서'로 써야 합니다.").detail("'으로서'는 자격, '으로써'는 수단을 나타냅니다. '선생으로서의 의무'는 선생이라는 위치를 의미하므로 '으로서'를 사용하여야 합니다. '매로써 학생들을 다스렸다'는 '매를 이용해서'를 의미하므로 '으로써'를 사용하여야 합니다.").build()