from src.engines.configs.spell_checker_config_builder import *
from src.models.interface import Tag, TagGroup, SpellErrorType

def rule() -> RuleBuilder:
    return RuleBuilder(SpellErrorType.COMPLEX)

_SPELLING_SPACING = [
    *rule()
    .tag(Tag.일반명사)
    .form("년도").if_not_spaced()
    .msg("'{dform[0]} 연도'가 올바른 표현입니다.").build(),
]

COMPLEX_ERRORS: list[KoSpellRules] = [
    *_SPELLING_SPACING,
]