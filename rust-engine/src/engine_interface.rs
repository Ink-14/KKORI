use phf::phf_map;
use pyo3::prelude::*;

#[derive(Debug)]
pub struct EnrichedToken {
    pub form_tag: u32,
    pub start: u32,
    pub end: u32,
    pub lemma: u16,
    pub len: u8,
    pub batchim: u8,
}

impl EnrichedToken {
    pub fn new(
        form: u32,
        tag: u8,
        start: u32,
        end: u32,
        lemma: u16,
        len: u8,
        batchim: u8,
    ) -> Self {
        debug_assert!(form < (1 << 25), "form exceeds 25 bits!");
        EnrichedToken {
            form_tag: (form << 7) | (tag as u32),
            start,
            end,
            lemma,
            len,
            batchim,
        }
    }

    pub fn form(&self) -> u32 {
        self.form_tag >> 7
    }

    pub fn tag(&self) -> u8 {
        (self.form_tag & 0x7F) as u8
    }
}

// #[pyclass] 제거 — 재귀 구조(Vec<Box<Condition>>)는 pyclass 불가,
// 파이썬에 노출할 필요도 없음 (py_types.rs의 xxxCondition들이 그 역할)
#[derive(PartialEq, Debug, Clone)]
pub enum Condition {
    Tag(u8),
    Form(u32),
    FormTag(u32),
    Length(u8),
    Batchim(u8),
    Lemma(u16),
    Any,
    AnyBatchim,
    NoBatchim,
    First,
    TagSet(u128),
    FormSet(Vec<u32>),
    And(Vec<Box<Condition>>),
    Or(Vec<Box<Condition>>),
    Not(Box<Condition>),
}

impl Condition {
    pub fn check_match(&self, token: &EnrichedToken) -> bool {
        match self {
            Condition::Tag(tag) => *tag == token.tag(),
            Condition::Form(form) => *form == token.form(),
            Condition::FormTag(formtag) => *formtag == token.form_tag,
            Condition::Length(length) => *length == token.len,
            Condition::Batchim(batchim) => *batchim == token.batchim,
            Condition::Lemma(lemma) => *lemma == token.lemma,
            Condition::Any => true,
            Condition::AnyBatchim => token.batchim > 1, // 0 = 한글 이외, 1 = 받침 없음
            Condition::NoBatchim => token.batchim == 1,
            Condition::First => token.start == 0,
            Condition::TagSet(mask) => (mask >> token.tag()) & 1 == 1,
            Condition::FormSet(forms) => forms.binary_search(&token.form()).is_ok(),
            Condition::And(conds) => conds.iter().all(|c| c.check_match(token)),
            Condition::Or(conds) => conds.iter().any(|c| c.check_match(token)),
            Condition::Not(cond) => !cond.check_match(token),
        }
    }

    pub fn tag_set(tags: impl IntoIterator<Item = u8>) -> Condition {
        let mut mask = 0u128;
        for tag in tags {
            mask |= 1u128 << tag;
        }
        Condition::TagSet(mask)
    }

    pub fn form_set(mut forms: Vec<u32>) -> Condition {
        forms.sort_unstable();
        forms.dedup();
        Condition::FormSet(forms)
    }

    pub fn and(conditions: impl IntoIterator<Item = Condition>) -> Condition {
        Condition::And(conditions.into_iter().map(Box::new).collect())
    }

    pub fn or(conditions: impl IntoIterator<Item = Condition>) -> Condition {
        Condition::Or(conditions.into_iter().map(Box::new).collect())
    }

    pub fn not(condition: Condition) -> Condition {
        Condition::Not(Box::new(condition))
    }
}

#[derive(PartialEq)]
pub enum SpacingRule {
    ANY = 0,
    SPACED,
    ATTACHED,
}

type RuleStep = (Condition, SpacingRule, bool, bool);

pub struct KoSpellRule {
    pub steps: Vec<RuleStep>,
    pub message: String,
    pub error_type: String,
    pub rule_id: String,
}

// pyclass enum은 unit variant만 허용 → 정수값 매핑은 유지
#[pyclass(eq, eq_int)]
#[derive(PartialEq, Debug, Clone)]
pub enum SpellErrorType {
    NotSet = 0,

    SpellingRaw = 1,
    SpacingRaw = 2,
    MeaningRaw = 3,
    LoanwordRaw = 4,

    Spacing = 5,
    Meaning = 6,
    Spelling = 7,
    Specific = 8,
    Loanword = 9,
    Warning = 10,

    NeedMLJudge = 11,

    Test = 999,
}

#[pyclass]
#[derive(PartialEq, Debug, Clone)]
pub struct SpellError {
    #[pyo3(get)]
    pub error_type: SpellErrorType,
    #[pyo3(get)]
    pub error_message: String,
    #[pyo3(get)]
    pub start_index: u32,
    #[pyo3(get)]
    pub end_index: u32,
    #[pyo3(get)]
    pub rule_id: String,
    #[pyo3(get)]
    pub debug_path: Option<String>,
}

pub static TAG2IDX: phf::Map<&'static str, u8> = phf_map! {
    "__UNK__"   => 0u8,
    "NNG"       => 1u8,
    "NNP"       => 2u8,
    "NNB"       => 3u8,
    "NR"        => 4u8,
    "NP"        => 5u8,
    "VV"        => 6u8,
    "VV-R"      => 7u8,
    "VV-I"      => 8u8,
    "VA"        => 9u8,
    "VA-R"      => 10u8,
    "VA-I"      => 11u8,
    "VX"        => 12u8,
    "VX-R"      => 13u8,
    "VX-I"      => 14u8,
    "VCP"       => 15u8,
    "VCN"       => 16u8,
    "MM"        => 17u8,
    "MAG"       => 18u8,
    "MAJ"       => 19u8,
    "IC"        => 20u8,
    "JKS"       => 21u8,
    "JKC"       => 22u8,
    "JKG"       => 23u8,
    "JKO"       => 24u8,
    "JKB"       => 25u8,
    "JKV"       => 26u8,
    "JKQ"       => 27u8,
    "JX"        => 28u8,
    "JC"        => 29u8,
    "EP"        => 30u8,
    "EF"        => 31u8,
    "EC"        => 32u8,
    "ETN"       => 33u8,
    "ETM"       => 34u8,
    "XPN"       => 35u8,
    "XSN"       => 36u8,
    "XSV"       => 37u8,
    "XSA"       => 38u8,
    "XSA-R"     => 39u8,
    "XSA-I"     => 40u8,
    "XSM"       => 41u8,
    "XR"        => 42u8,
    "SF"        => 43u8,
    "SP"        => 44u8,
    "SS"        => 45u8,
    "SSO"       => 46u8,
    "SSC"       => 47u8,
    "SE"        => 48u8,
    "SO"        => 49u8,
    "SW"        => 50u8,
    "SL"        => 51u8,
    "SH"        => 52u8,
    "SN"        => 53u8,
    "SB"        => 54u8,
    "UN"        => 55u8,
    "W_URL"     => 56u8,
    "W_EMAIL"   => 57u8,
    "W_HASHTAG" => 58u8,
    "W_MENTION" => 59u8,
    "W_SERIAL"  => 60u8,
    "W_EMOJI"   => 61u8,
    "Z_CODA"    => 62u8,
    "Z_SIOT"    => 63u8,
    "USER0"     => 64u8,
    "USER1"     => 65u8,
    "USER2"     => 66u8,
    "USER3"     => 67u8,
    "USER4"     => 68u8,
};

pub static BATCHIM2IDX: phf::Map<&'static str, u8> = phf_map! {
    "__UNK__" => 0u8,
    ""        => 1u8,
    "ᆨ"      => 2u8,
    "ᆩ"      => 3u8,
    "ᆪ"      => 4u8,
    "ᆫ"      => 5u8,
    "ᆬ"      => 6u8,
    "ᆭ"      => 7u8,
    "ᆮ"      => 8u8,
    "ᆯ"      => 9u8,
    "ᆰ"      => 10u8,
    "ᆱ"      => 11u8,
    "ᆲ"      => 12u8,
    "ᆳ"      => 13u8,
    "ᆴ"      => 14u8,
    "ᆵ"      => 15u8,
    "ᆶ"      => 16u8,
    "ᆷ"      => 17u8,
    "ᆸ"      => 18u8,
    "ᆹ"      => 19u8,
    "ᆺ"      => 20u8,
    "ᆻ"      => 21u8,
    "ᆼ"      => 22u8,
    "ᆽ"      => 23u8,
    "ᆾ"      => 24u8,
    "ᆿ"      => 25u8,
    "ᇀ"      => 26u8,
    "ᇁ"      => 27u8,
    "ᇂ"      => 28u8,
};