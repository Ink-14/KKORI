from src.engines.configs.rule_builder import *
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
    rule = RuleBuilder(SpellErrorType.SPACING).tag_form(Tag.일반명사, nng1).tag_form(Tag.일반명사, nng2)
    
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
    
def VV_EC_VV(vv1: tuple[str, str], ec: str, vv2: tuple[str, str], spacing_rule: SpacingRule, message = None, detail = None) -> list[KoSpellRules]:
    vv1_form, vv1_tag = vv1
    vv2_form, vv2_tag = vv2
    rule = RuleBuilder(SpellErrorType.SPACING).tag_form(Tag[vv1_tag], vv1_form).tag_form(Tag.연결어미, ec).tag_form(Tag[vv2_tag], vv2_form)

    message1 = f"merge((\"{vv1_form}\", \"{vv1_tag}\"), (\"{ec}\", \"연결어미\"))"
    message2 = f"merge((\"{vv2_form}\", \"{vv2_tag}\"), (\"다\", \"연결어미\"))"
    
    if spacing_rule == SpacingRule.SPACED:
        rule.if_not_spaced().msg(f"'{message1} {message2}'로 띄어 써야 합니다.")
    elif spacing_rule == SpacingRule.ATTACHED:
        rule.if_spaced().msg(f"'{message1}{message2}'로 붙여 써야 합니다.")
    elif spacing_rule == SpacingRule.ANY:
        if message is None:
            raise ValueError("you must set error message to function 'NNG_and_some' if spacing rule is SpacingRule.ANY.")
        rule.msg(message)

    if detail:
        rule.detail(detail)

    return rule.build()