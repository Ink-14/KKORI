from src.engines.configs.rule_builder import *
from src.models.interface import Tag, TagGroup, SpellErrorType

def rule() -> RuleBuilder:
    return RuleBuilder(SpellErrorType.WARNING)

# 토크나이저 오분석 잦은 규칙 / 문맥 판단 필요한 규칙
WARNINGS = [
    *rule()
    .tag_form(Tag.동사, "두르")
    .tag_form(Tag.연결어미, "어")
    .tag_form(Tag.보조용언, "보")
    .if_spaced()
    .msg("'살펴보다'의 의미인 '둘러보다'는 붙여 써야 합니다.")
    .build(),

    *rule()
    .any()
    .tag_form(Tag.긍정지정사, "이")
    .if_spaced()
    .msg("'이다'를 앞 말과 붙여 써야 합니다.")
    .build(),
]