from src.engines.configs.rule_builder import RuleBuilder, AND, OR, NOT, tag, tags, tag_form, form, forms, lemma, batchim, longer, SpacingRule, KoSpellRules
from src.models.interface import Tag, TagGroup, SpellErrorType

def rule() -> RuleBuilder:
    return RuleBuilder(SpellErrorType.MEANING)

MEANING_CONFLICT_ERRORS: list[KoSpellRules] = [
    *rule().id("MEANING_미리_예")
    .tag_form(Tag.일반부사, "미리")
    .AND(tag(Tag.일반명사), forms({"예견", "예방", "예언", "예습", "예고", "예측", "예약", "예단", "예매"}))
    .msg("'미리'에 이미 '예(豫)'의 의미가 포함되어 있습니다.").build(),

    *rule().id("MEANING_부상_입다")
    .tag_form(Tag.일반명사, "부상")
    .any().opt()
    .tag_form(Tag.동사불규칙활용, "입")
    .msg("'부상'에 '입다'의 뜻이 포함되어 있습니다. '부상 당하다' 등으로 쓸 것을 권장합니다.").build(),
    
    *rule().id("MEANING_OO_소리")
    .AND(tag(Tag.일반명사), forms({"비명", "신음", "함성"}))
    .tag_form(Tag.일반명사, "소리")
    .msg("'비명/신음/함성'에 이미 '소리'의 의미가 포함되어 있습니다. '소리'를 삭제하는 것을 권장합니다.").build(),
    
    *rule().id("MEANING_다시_되")
    .tag_form(Tag.일반부사, "다시")
    .AND(tag(Tag.동사), forms({"되돌이키", "되돌리"}))
    .msg("'다시'에 이미 '되-'의 의미가 포함되어 있습니다.").build(),

    *rule().id("MEANING_다시_회복")
    .tag_form(Tag.일반부사, "다시")
    .AND(tag(Tag.일반명사), forms({"회복"}))
    .msg("'회복(回復)'에 이미 '다시'의 의미가 포함되어 있습니다.").build(),
    
    *rule().id("MEANING_다시_재_명사")
    .tag_form(Tag.일반부사, "다시")
    .AND(tag(Tag.일반명사), forms({"재건", "재회", "재개"}))
    .msg("'다시'에 이미 '재(再)'의 의미가 포함되어 있습니다.").build(),

    *rule().id("MEANING_다시_재_체언접두사")
    .tag_form(Tag.일반부사, "다시")
    .tag_form(Tag.체언접두사, "재")
    .NOT(form("방송")).context()
    .msg("'다시'에 이미 '재(再)'의 의미가 포함되어 있습니다.").build(),
    
    *rule().id("MEANING_전_앞")
    .AND(tag(Tag.일반명사), forms({"역전", "영전"}))
    .tag_form(Tag.일반명사, "앞")
    .msg("'전(前)'에 이미 '앞'의 의미가 포함되어 있습니다.").build(),

    *rule().id("MEANING_이견")
    .tag_form(Tag.관형사, "다른")
    .tag_form(Tag.일반명사, "이견")
    .msg("'이견(異見)'에 이미 '다른'의 의미가 포함되어 있습니다. '다른 의견' 혹은 '이견'으로만 쓸 것을 권장합니다.").build(),

    *rule().id("MEANING_매OO마다")
    .tag_form(Tag.관형사, "매").context()
    .any().context()
    .tag_form(Tag.보조사, "마다")
    .msg("'매(每)'에 이미 '마다'의 의미가 포함되어 있습니다.").build(),
    
    *rule().id("MEANING_당일 날")
    .tag_form(Tag.일반명사, "당일")
    .tag_form(Tag.일반명사, "날")
    .msg("'당일'에 이미 '날'의 의미가 포함되어 있습니다.").build(),
]