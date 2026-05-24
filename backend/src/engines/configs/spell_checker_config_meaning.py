from src.engines.configs.spell_checker_config_builder import *
from src.models.interface import Tag, TagGroup, SpellErrorType

def rule() -> RuleBuilder:
    return RuleBuilder(SpellErrorType.MEANING)

MEANING_CONFLICT_ERRORS: list[KoSpellRules] = [
    *rule()
    .tag_form(Tag.일반부사, "미리")
    .AND(tag(Tag.일반명사), forms({"예견", "예방", "예언", "예습", "예고"}))
    .msg("'미리'에 '예(予)'의 의미가 들어 있습니다.")
    .build(),

    *rule()
    .tag_form(Tag.일반명사, "부상")
    .tag_form(Tag.동사불규칙활용, "입")
    .msg("'부상'에 '입다'의 뜻이 포함되어 있습니다. '부상 당하다' 등으로 쓸 것을 권장합니다.")
    .build(),
    
    *rule()
    .AND(tag(Tag.일반명사), forms({"비명", "신음", "함성"}))
    .tag_form(Tag.일반명사, "소리")
    .msg("'비명/신음/함성'에 이미 '소리'의 의미가 포함되어 있습니다. '소리'를 삭제하는 것을 권장합니다.")
    .build(),
    
    *rule()
    .tag_form(Tag.일반부사, "다시")
    .AND(tag(Tag.동사), forms({"되돌이키", "되돌리"}))
    .msg("'다시'에 이미 '되-'의 의미가 포함되어 있습니다.")
    .build(),
    
    *rule()
    .tag_form(Tag.일반부사, "다시")
    .AND(tag(Tag.일반명사), forms({"재건"}))
    .msg("'다시'에 이미 '되-'의 의미가 포함되어 있습니다.")
    .build(),
    
    *rule()
    .AND(tag(Tag.일반명사), forms({"역전", "영전"}))
    .tag_form(Tag.일반명사, "앞")
    .msg("'전(前)'에 이미 '앞'의 의미가 포함되어 있습니다.")
    .build(),
]