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
    ATTACHED
}

type RuleStep = (Condition, SpacingRule, bool, bool);

pub struct KoSpellRule {
    pub steps: Vec<RuleStep>,
    pub message: String,
    pub error_type: String,
    pub rule_id: String,
}

#[derive(PartialEq, Debug, Clone)]
pub enum SpellErrorType {
    NotSet = 0,

    SpellingRaw,
    SpacingRaw,
    MeaningRaw,
    LoanwordRaw,

    Spacing,
    Meaning,
    Spelling,
    Specific,
    Loanword,

    Warning,
    NeedMLJudge,

    Test,
}

#[derive(PartialEq, Debug, Clone)]
pub struct SpellError {
    pub error_type: SpellErrorType,
    pub error_message: String,
    pub start_index: u32,
    pub end_index: u32,
    pub rule_id: String,
    pub debug_path: Option<String>
}