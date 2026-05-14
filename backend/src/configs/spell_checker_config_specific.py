from src.configs.spell_checker_config_builder import *
from src.models.interface import Tag, TagGroup, SpellErrorType

def rule() -> RuleBuilder:
    return RuleBuilder(SpellErrorType.SPECIFIC)

KIWI_EXCEPTION_ERRORS: list[KoSpellRules] = [
    # 토크나이저 비정상 동작에 따른 특수 룰 정의

    *rule() # '제일가다'. 보통 '제일가는'의 형태가 쓰이므로 '제일가는'만 검출.
    .tag_form(Tag.체언접두사, "제")
    .tag_form(Tag.수사, "일")
    .tag_form(Tag.동사, "가")
    .if_spaced()
    .tag_form(Tag.관형사형전성어미, "는")
    .msg("'제일가다'는 한 단어이므로 붙여 써야 합니다.")
    .build(),

    *rule() # ~래냐가 '래+이+냐로 쪼개져서 특수 대응.
    .tag_form(Tag.종결어미, "래")
    .tag_form(Tag.긍정지정사, "이")
    .tag_form(Tag.종결어미, "냐")
    .msg("'~라냐'가 올바른 표현입니다.")
    .build(),
]
