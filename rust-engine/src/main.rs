mod engine_interface;
use std::{collections::VecDeque};

use engine_interface::{EnrichedToken, Condition, SpacingRule, KoSpellRule, SpellError, SpellErrorType};
use rustc_hash::{FxHashMap, FxHashSet};

struct Transition {
    condition: Condition,
    target_node: usize,
    spacing_rule: SpacingRule,
    is_optional: bool,
    is_context: bool,
}

impl Transition {
    fn new (condition: Condition, target_node: usize, spacing_rule: SpacingRule, is_optional: bool, is_context: bool) -> Self {
        Transition { 
            condition,
            target_node,
            spacing_rule,
            is_optional,
            is_context
        }
    }
}

struct RuleNode {
    tag_transitions: FxHashMap<u8, Vec<usize>>,
    form_transitions: FxHashMap<u32, Vec<usize>>,
    form_and_tag_transitions: FxHashMap<u32, Vec<usize>>,
    batchim_transitions: Option<Box<[Option<Vec<usize>>; 29]>>,
    any_batchim_transitions: Vec<usize>,
    fallback_transitions: Vec<usize>,

    output_message: Option<String>,
    rule_id: Option<String>,
    error_type: SpellErrorType,
}

impl RuleNode {
    fn new() -> Self {
        RuleNode {
            tag_transitions: FxHashMap::default(),
            form_transitions: FxHashMap::default(),
            form_and_tag_transitions: FxHashMap::default(),
            batchim_transitions: None,
            any_batchim_transitions: Vec::new(),
            fallback_transitions: Vec::new(),

            output_message: None,
            rule_id: None,
            error_type: SpellErrorType::NotSet,
        }
    }

    fn find_transition(&self, transitions: &[Transition], cond: &Condition, spacing: &SpacingRule, is_optional: bool, is_context: bool) -> Option<usize> {
        let candidates: &[usize] = match cond {
            Condition::Tag(tag) => {
                self.tag_transitions.get(&tag).map_or(&[], |v| v.as_slice())
            }
            Condition::Form(form) => {
                self.form_transitions.get(&form).map_or(&[], |v| v.as_slice())
            }
            Condition::FormTag(ft) => {
                self.form_and_tag_transitions.get(&ft).map_or(&[], |v| v.as_slice())
            }
            Condition::Batchim(b) => {
                self.batchim_transitions.as_deref().and_then(|arr| arr[*b as usize].as_deref()).unwrap_or(&[])
            }
            Condition::AnyBatchim => &self.any_batchim_transitions,
            _ => {
                return self.fallback_transitions.iter().copied().find(|&ti| {
                    let t = &transitions[ti];
                    t.condition == *cond && t.spacing_rule == *spacing && t.is_optional == is_optional && t.is_context == is_context
                    });
                }
            };
        
        candidates.iter().copied().find(|&ti| {
            let t = &transitions[ti];
            t.spacing_rule == *spacing && t.is_optional == is_optional && t.is_context == is_context
        })
    }

    fn add_transition_idx(&mut self, cond: Condition, trans_idx: usize) {
        match cond {
            Condition::Tag(tag) => {
                self.tag_transitions.entry(tag).or_default().push(trans_idx);
            }
            Condition::Form(form) => {
                self.form_transitions.entry(form).or_default().push(trans_idx);
            }
            Condition::FormTag(form_tag) => {
                self.form_and_tag_transitions.entry(form_tag).or_default().push(trans_idx);
            }
            Condition::Batchim(b) => {
                let arr = self.batchim_transitions.get_or_insert_with(|| Box::new(std::array::from_fn(|_| None)));
                arr[b as usize].get_or_insert_with(Vec::new).push(trans_idx);
            }
            Condition::AnyBatchim => {
                self.any_batchim_transitions.push(trans_idx);
            }
            _ => {
                self.fallback_transitions.push(trans_idx);
            }
        }
    }

    fn iter_all_transitions(&self) -> impl Iterator<Item = &usize> {
        let batchim_iter = self.batchim_transitions
            .iter()
            .flat_map(|arr| arr.iter())
            .flat_map(|slot| slot.iter())
            .flat_map(|v| v.iter());

        self.fallback_transitions.iter()
            .chain(self.any_batchim_transitions.iter())
            .chain(self.tag_transitions.values().flat_map(|v| v.iter()))
            .chain(self.form_transitions.values().flat_map(|v| v.iter()))
            .chain(self.form_and_tag_transitions.values().flat_map(|v| v.iter()))
            .chain(batchim_iter)
    }
}

pub struct RuleCheckerBuilder {
    nodes: Vec<RuleNode>,
    transitions: Vec<Transition>,
    form_vec: FxHashMap<String, u32>,
    lemma_vec: FxHashMap<String, u16>
}

impl RuleCheckerBuilder {
    pub fn new() -> Self {
        let mut builder = RuleCheckerBuilder {
            nodes: Vec::new(),
            transitions: Vec::new(),
            form_vec: FxHashMap::default(),
            lemma_vec: FxHashMap::default(),
        };
        builder.add_node();
        builder.form_vec.insert("__UNK__".to_string(), 0u32);
        builder.lemma_vec.insert("__UNK__".to_string(), 0u16);
        builder
    }

    pub fn add_rule(&mut self, rule: KoSpellRule) {
        if rule.steps.is_empty() { return; }

        let mut current: usize = 0;

        for (cond, spacing, optional, context) in rule.steps {
            current = self.get_or_create_next_node(current, cond, spacing, optional, context);
        }

        self.nodes[current].output_message = Some(rule.message);
    }

    pub fn build(self) -> RuleChecker {
        let optional_closure = self.compute_optional_closure();
        let eof_closure = self.compute_eof_closure();
        let bos_epsilon = self.compute_bos_epsilon();

        RuleChecker {
            nodes: self.nodes,
            transitions: self.transitions,
            optional_closure,
            eof_closure,
            bos_epsilon,
        }
    }

    fn add_node(&mut self) -> usize {
        let id = self.nodes.len();
        self.nodes.push(RuleNode::new());
        id
    }

    fn get_or_create_next_node(&mut self, node_idx:usize, cond: Condition, spacing: SpacingRule, is_optional: bool, is_context: bool) -> usize {
        let existing = self.nodes[node_idx].find_transition(&self.transitions, &cond, &spacing, is_optional, is_context);

        if let Some(trans_idx) = existing {
            return self.transitions[trans_idx].target_node;
        }

        let next_node_idx = self.add_node();
        let trans_idx = self.transitions.len();
        self.transitions.push(Transition::new(cond.clone(), next_node_idx, spacing, is_optional, is_context));

        self.nodes[node_idx].add_transition_idx(cond, trans_idx);

        next_node_idx
    }

    fn compute_optional_closure(&self) -> Vec<Vec<usize>> {
        let n = self.nodes.len();
        let mut optional_closure: Vec<Vec<usize>> = Vec::with_capacity(n);

        for node_idx in 0..n {
            let mut closure: Vec<usize> = vec![node_idx];
            let mut queue: VecDeque<usize> = VecDeque::from([node_idx]);

            while let Some(current) = queue.pop_front() {
                for &trans_idx in self.nodes[current].iter_all_transitions() {
                    let trans = &self.transitions[trans_idx];
                    if trans.is_optional && !closure.contains(&trans.target_node) {
                        closure.push(trans.target_node);
                        queue.push_back(trans.target_node);
                    }
                }
            }

            optional_closure.push(closure);
        }

        optional_closure
    }

    fn compute_eof_closure(&self) -> Vec<Vec<usize>> {
        let n = self.nodes.len();
        let mut eof_closure: Vec<Vec<usize>> = Vec::with_capacity(n);

        for node_idx in 0..n {
            let mut closure: FxHashSet<usize> = FxHashSet::default();
            closure.insert(node_idx);
            let mut queue: VecDeque<usize> = VecDeque::from([node_idx]);

            while let Some(current) = queue.pop_front() {
                for &trans_idx in self.nodes[current].iter_all_transitions() {
                    let trans = &self.transitions[trans_idx];
                    let is_not_any = matches!(&trans.condition, Condition::Not(_))
                        && trans.spacing_rule == SpacingRule::ANY
                        && trans.is_context;

                    if (trans.is_optional || is_not_any) && !closure.contains(&trans.target_node) {
                        closure.insert(trans.target_node);
                        queue.push_back(trans.target_node);
                    }
                }
            }

            eof_closure.push(closure.into_iter().collect());
        }

        eof_closure
    }

    fn compute_bos_epsilon(&self) -> Vec<usize> {
        let mut result: FxHashSet<usize> = FxHashSet::default();
        let mut queue: VecDeque<usize> = VecDeque::new();

        for &trans_idx in self.nodes[0].iter_all_transitions() {
            let trans = &self.transitions[trans_idx];
            if matches!(&trans.condition, Condition::Not(_)) && trans.spacing_rule == SpacingRule::ANY && trans.is_context && result.insert(trans.target_node) {
                queue.push_back(trans.target_node);
            }
        }

        while let Some(current) = queue.pop_front() {
            for &trans_idx in self.nodes[current].iter_all_transitions() {
                let trans = &self.transitions[trans_idx];
                if matches!(&trans.condition, Condition::Not(_)) && trans.spacing_rule == SpacingRule::ANY && trans.is_context && result.insert(trans.target_node) {
                    queue.push_back(trans.target_node);
                }
            }
        }

        result.into_iter().collect()
    }
}

pub struct RuleChecker {
    nodes: Vec<RuleNode>,
    transitions: Vec<Transition>,
    optional_closure: Vec<Vec<usize>>,
    eof_closure: Vec<Vec<usize>>,
    bos_epsilon: Vec<usize>
}

impl RuleChecker {
    pub fn check(&self, tokens: Vec<EnrichedToken>) -> Vec<SpellError> {
        if tokens.is_empty() { return Vec::new(); }

        let mut errors: Vec<SpellError> = Vec::new();
        let mut active_cursors: FxHashMap<usize, (Option<usize>, usize)> = FxHashMap::default();
        let mut next_cursors: FxHashMap<usize, (Option<usize>, usize)> = FxHashMap::default();
        let mut expanded_cursors: FxHashMap<usize, (Option<usize>, usize)> = FxHashMap::default();
        let mut candidates: Vec<usize> = Vec::new();
        let mut yielded_outputs: FxHashSet<(usize, usize)> = FxHashSet::default();

        for (i, token) in tokens.iter().enumerate() {
            let has_space = if i > 0 { token.start - tokens[i-1].end > 0 } else { false };

            expanded_cursors.clear();

            // ── Phase 1: epsilon closure ──
            if i == 0 {
                for &node_idx in &self.bos_epsilon {
                    expanded_cursors.insert(node_idx, (None, 0));
                }
            }

            active_cursors.insert(0, (None, i));
            Self::expand_cursors(&active_cursors, &self.optional_closure, &mut expanded_cursors);

            // ── Phase 2: 출력 수집 & 전이 탐색 ──
            next_cursors.clear();
            let mut current_step_errors: FxHashMap<(usize, usize), SpellError> = FxHashMap::default();

            for (&node_idx, &(start_idx, end_idx)) in &expanded_cursors {
                let node = &self.nodes[node_idx];

                // 2-A: 출력 수집
                if let Some(start_token_idx) = start_idx {
                    if start_token_idx < i && !yielded_outputs.contains(&(node_idx, start_token_idx)) {
                        yielded_outputs.insert((node_idx, start_token_idx));
                        self.collect_error(&tokens, node_idx, start_token_idx, end_idx, &mut current_step_errors);
                    }
                }

                // 2-B: 후보 전이 수집
                candidates.clear();

                if let Some(trans_indices) = node.tag_transitions.get(&token.tag()) {
                    candidates.extend_from_slice(trans_indices);
                }
                if token.form() > 0 {
                    if let Some(trans_indices) = node.form_transitions.get(&token.form()) {
                        candidates.extend_from_slice(trans_indices);
                    }
                    if let Some(trans_indices) = node.form_and_tag_transitions.get(&token.form_tag) {
                        candidates.extend_from_slice(trans_indices);
                    }
                }
                if token.batchim > 0 {
                    if let Some(arr) = &node.batchim_transitions {
                        if let Some(trans_indices) = &arr[token.batchim as usize] {
                            candidates.extend_from_slice(trans_indices);
                        }
                    }
                    if token.batchim > 1 {
                        candidates.extend_from_slice(&node.any_batchim_transitions);
                    }
                    for &trans_idx in &node.fallback_transitions {
                        let trans = &self.transitions[trans_idx];
                        if trans.condition.check_match(token) {
                            candidates.push(trans_idx);
                        }
                    }
                }

                // 2-C: spacing 필터 + next_cursors 업데이트
                for &trans_idx in &candidates {
                    let trans = &self.transitions[trans_idx];
                    match trans.spacing_rule {
                        SpacingRule::SPACED if !has_space => continue,
                        SpacingRule::ATTACHED if has_space => continue,
                        _ => {}
                    }

                    let target = trans.target_node;
                    let new_start = if start_idx.is_none() && !trans.is_context { Some(i) } else { start_idx };
                    let new_end = if !trans.is_context { i } else { end_idx };

                    let entry = next_cursors.entry(target).or_insert((new_start, new_end));
                    if Self::is_later_start(new_start, entry.0) {
                        *entry = (new_start, new_end);
                    }
                }
            }

            // ── Phase 3: 에러 수집 & 커서 스왑 ──
            for (_, err) in current_step_errors {
                errors.push(err);
            }
            std::mem::swap(&mut active_cursors, &mut next_cursors);
        }

        // ── EOF epsilon ──
        let mut final_expanded: FxHashMap<usize, (Option<usize>, usize)> = FxHashMap::default();
        Self::expand_cursors(&active_cursors, &self.eof_closure, &mut final_expanded);

        let mut final_step_errors: FxHashMap<(usize, usize), SpellError> = FxHashMap::default();

        for (node_idx, (start_idx, end_idx)) in final_expanded {
            let Some(start_token_idx) = start_idx else { continue; };
            if yielded_outputs.contains(&(node_idx, start_token_idx)) { continue; }
            self.collect_error(&tokens, node_idx, start_token_idx, end_idx, &mut final_step_errors);
        }

        for (_, err) in final_step_errors {
            errors.push(err);
        }

        errors
    }

    fn is_later_start(new: Option<usize>, old: Option<usize>) -> bool {
        match (new, old) {
            (None, _) => false,
            (Some(_), None) => true,
            (Some(a), Some(b)) => a > b,
        }
    }

    fn update_shortest_match(
        storage: &mut FxHashMap<(usize, usize), SpellError>,
        node_idx: usize,
        start_token_idx: usize,
        error: SpellError,
    ) {
        let key = (node_idx, start_token_idx);
        match storage.get(&key) {
            None => { storage.insert(key, error); }
            Some(existing) => {
                let old_len = existing.end_index - existing.start_index;
                let new_len = error.end_index - error.start_index;
                if new_len < old_len || (new_len == old_len && error.start_index > existing.start_index) {
                    storage.insert(key, error);
                }
            }
        }
    }

    fn collect_error(
        &self,
        tokens: &[EnrichedToken],
        node_idx: usize,
        start_token_idx: usize,
        end_idx: usize,
        storage: &mut FxHashMap<(usize, usize), SpellError>,
    ) {
        let node = &self.nodes[node_idx];
        let Some(msg) = &node.output_message else { return; };
        let err = SpellError {
            error_type: node.error_type.clone(),
            error_message: msg.clone(),
            start_index: tokens[start_token_idx].start,
            end_index: tokens[end_idx].end,
            rule_id: node.rule_id.clone().unwrap_or_default(),
            debug_path: None,
        };
        Self::update_shortest_match(storage, node_idx, start_token_idx, err);
    }

    fn expand_cursors(
        source: &FxHashMap<usize, (Option<usize>, usize)>,
        closure: &[Vec<usize>],
        target: &mut FxHashMap<usize, (Option<usize>, usize)>,
    ) {
        for (&node_idx, &idxs) in source {
            for &closure_node in &closure[node_idx] {
                let entry = target.entry(closure_node).or_insert(idxs);
                if Self::is_later_start(idxs.0, entry.0) {
                    *entry = idxs;
                }
            }
        }
    }
}

fn main() {
    let t = EnrichedToken::new(1, 1, 1, 1, 16, 2, 1);
    let cond = Condition::Tag(1);
    let res = cond.check_match(&t);
    println!("{:#?}", res);
}