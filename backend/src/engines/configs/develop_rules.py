from src.engines.configs.rule_builder import *
from src.models.interface import Tag, TagGroup, SpellErrorType
from src.engines.configs import rule_meaning, rule_spacing, rule_specific, rule_spelling, rule_warning, rule_complex, rule_proofread, rule_model
from src.engines.configs.rule_constants import *

def rule() -> RuleBuilder:
    return RuleBuilder(SpellErrorType.TEST)

digging = [
    *rule().id("digging_직")
    .tag(Tag.일반명사)
    .tag_form(Tag.일반명사, "직").if_spaced()
    .msg("{dform[0]}").build(),
]