use std::collections::VecDeque;

use pyo3::prelude::*;
use pyo3::types::PyList;
use rustc_hash::{FxHashMap, FxHashSet};

use crate::engine_interface::{EnrichedToken, Condition, SpacingRule, TAG2IDX, BATCHIM2IDX};
use crate::py_types::*;

struct Transition {
    condition: Condition,
    target_node: usize,
    spacing_rule: SpacingRule,
    is_optional: bool,
    is_context: bool,
}

impl Transition {
    fn new(condition: Condition, target_node: usize, spacing_rule: SpacingRule, is_optional: bool, is_context: bool) -> Self {
        Transition { condition, target_node, spacing_rule, is_optional, is_context }
    }
}

struct RuleNode {
    tag_transitions: FxHashMap<u8, Vec<usize>>,
    form_transitions: FxHashMap<u32, Vec<usize>>,
    form_and_tag_transitions: FxHashMap<u32, Vec<usize>>,
    batchim_transitions: Option<Box<[Option<Vec<usize>>; 29]>>,
    any_batchim_transitions: Vec<usize>,
    fallback_transitions: Vec<usize>,

    match_id: Option<u32>,
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

            match_id: None,
        }
    }

    fn find_transition(&self, transitions: &[Transition], cond: &Condition, spacing: &SpacingRule, is_optional: bool, is_context: bool) -> Option<usize> {
        let candidates: &[usize] = match cond {
            Condition::Tag(tag) => self.tag_transitions.get(tag).map_or(&[], |v| v.as_slice()),
            Condition::Form(form) => self.form_transitions.get(form).map_or(&[], |v| v.as_slice()),
            Condition::FormTag(ft) => self.form_and_tag_transitions.get(ft).map_or(&[], |v| v.as_slice()),
            Condition::Batchim(b) => {
                self.batchim_transitions.as_deref()
                    .and_then(|arr| arr[*b as usize].as_deref())
                    .unwrap_or(&[])
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

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// RuleCheckerBuilder
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

#[pyclass]
pub struct RuleCheckerBuilder {
    nodes: Vec<RuleNode>,
    transitions: Vec<Transition>,
    form_vec: FxHashMap<String, u32>,
    lemma_vec: FxHashMap<String, u16>,
}

#[pymethods]
impl RuleCheckerBuilder {
    #[new]
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

    pub fn add_rule(
        &mut self,
        py: Python,
        steps: Vec<(PyObject, PyObject, bool, bool)>,
        match_id: u32,
    ) -> PyResult<()> {
        if steps.is_empty() { return Ok(()); }

        let mut current: usize = 0;

        for (cond_obj, spacing_obj, is_optional, is_context) in &steps {
            let spacing = match spacing_obj.extract::<i32>(py)? {
                0 => SpacingRule::ANY,
                1 => SpacingRule::SPACED,
                2 => SpacingRule::ATTACHED,
                v => return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(
                    format!("unknown SpacingRule: {v}")
                )),
            };

            let cond = self.intern_condition(py, cond_obj)?;
            current = self.get_or_create_next_node(current, cond, spacing, *is_optional, *is_context);
        }

        self.nodes[current].match_id = Some(match_id);
        Ok(())
    }

    pub fn build(&mut self) -> RuleChecker {
        let optional_closure = self.compute_optional_closure();
        let eof_closure      = self.compute_eof_closure();
        let bos_epsilon      = self.compute_bos_epsilon();

        RuleChecker {
            nodes:            std::mem::take(&mut self.nodes),
            transitions:      std::mem::take(&mut self.transitions),
            optional_closure,
            eof_closure,
            bos_epsilon,
            form_dict:  std::mem::take(&mut self.form_vec),
            lemma_dict: std::mem::take(&mut self.lemma_vec),
        }
    }
}

impl RuleCheckerBuilder {
    fn add_node(&mut self) -> usize {
        let id = self.nodes.len();
        self.nodes.push(RuleNode::new());
        id
    }

    fn get_or_create_next_node(&mut self, node_idx: usize, cond: Condition, spacing: SpacingRule, is_optional: bool, is_context: bool) -> usize {
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
        let mut closures: Vec<Vec<usize>> = vec![Vec::new(); n];

        let mut seen = vec![0usize; n];
        let mut stamp = 1usize;

        for node_idx in (0..n).rev() {
            let mut closure = Vec::new();

            seen[node_idx] = stamp;
            closure.push(node_idx);

            for &trans_idx in self.nodes[node_idx].iter_all_transitions() {
                let trans = &self.transitions[trans_idx];

                if trans.is_optional {
                    debug_assert!(
                        trans.target_node > node_idx,
                        "optional closure assumes acyclic forward node indices"
                    );

                    for &reachable in &closures[trans.target_node] {
                        if seen[reachable] != stamp {
                            seen[reachable] = stamp;
                            closure.push(reachable);
                        }
                    }
                }
            }

            closures[node_idx] = closure;
            stamp += 1;
        }

        closures
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
            if matches!(&trans.condition, Condition::Not(_))
                && trans.spacing_rule == SpacingRule::ANY
                && trans.is_context
                && result.insert(trans.target_node)
            {
                queue.push_back(trans.target_node);
            }
        }

        while let Some(current) = queue.pop_front() {
            for &trans_idx in self.nodes[current].iter_all_transitions() {
                let trans = &self.transitions[trans_idx];
                if matches!(&trans.condition, Condition::Not(_))
                    && trans.spacing_rule == SpacingRule::ANY
                    && trans.is_context
                    && result.insert(trans.target_node)
                {
                    queue.push_back(trans.target_node);
                }
            }
        }

        result.into_iter().collect()
    }

    fn intern_condition(&mut self, py: Python, obj: &PyObject) -> PyResult<Condition> {
        let obj = obj.bind(py);

        if let Ok(c) = obj.downcast::<TagCondition>() {
            let borrowed = c.borrow();
            let idx = TAG2IDX.get(borrowed.tag.as_str())
                .copied()
                .ok_or_else(|| PyErr::new::<pyo3::exceptions::PyValueError, _>(
                    format!("unknown tag: {}", borrowed.tag)
                ))?;
            return Ok(Condition::Tag(idx));
        }

        if let Ok(c) = obj.downcast::<FormCondition>() {
            let form = c.borrow().form.clone();
            let next = self.form_vec.len() as u32;
            let idx = *self.form_vec.entry(form).or_insert(next);
            return Ok(Condition::Form(idx));
        }

        if let Ok(c) = obj.downcast::<TagAndFormCondition>() {
            let b = c.borrow();
            let tag_idx = TAG2IDX.get(b.tag.as_str())
                .copied()
                .ok_or_else(|| PyErr::new::<pyo3::exceptions::PyValueError, _>(
                    format!("unknown tag: {}", b.tag)
                ))?;
            let form = b.form.clone();
            drop(b);
            let next = self.form_vec.len() as u32;
            let form_idx = *self.form_vec.entry(form).or_insert(next);
            return Ok(Condition::FormTag((form_idx << 7) | tag_idx as u32));
        }

        if let Ok(c) = obj.downcast::<LemmaCondition>() {
            let lemma = c.borrow().lemma.clone();
            let next = self.lemma_vec.len() as u16;
            let idx = *self.lemma_vec.entry(lemma).or_insert(next);
            return Ok(Condition::Lemma(idx));
        }

        if obj.downcast::<AnyCondition>().is_ok() {
            return Ok(Condition::Any);
        }
        if obj.downcast::<AnyBatchimCondition>().is_ok() {
            return Ok(Condition::AnyBatchim);
        }
        if obj.downcast::<NoBatchimCondition>().is_ok() {
            return Ok(Condition::NoBatchim);
        }
        if obj.downcast::<FirstTokenCondition>().is_ok() {
            return Ok(Condition::First);
        }

        if let Ok(c) = obj.downcast::<BatchimCondition>() {
            let borrowed = c.borrow();
            let idx = BATCHIM2IDX.get(borrowed.batchim.as_str())
                .copied()
                .ok_or_else(|| PyErr::new::<pyo3::exceptions::PyValueError, _>(
                    format!("unknown batchim: {}", borrowed.batchim)
                ))?;
            return Ok(Condition::Batchim(idx));
        }

        if let Ok(c) = obj.downcast::<LengthCondition>() {
            return Ok(Condition::Length(c.borrow().length));
        }

        if let Ok(c) = obj.downcast::<TagSetCondition>() {
            let tags = c.borrow().tags.iter()
                .map(|t| TAG2IDX.get(t.as_str()).copied()
                    .ok_or_else(|| PyErr::new::<pyo3::exceptions::PyValueError, _>(
                        format!("unknown tag: {t}")
                    )))
                .collect::<PyResult<Vec<u8>>>()?;
            return Ok(Condition::tag_set(tags));
        }

        if let Ok(c) = obj.downcast::<FormSetCondition>() {
            let forms = c.borrow().forms.iter()
                .map(|f| {
                    let next = self.form_vec.len() as u32;
                    *self.form_vec.entry(f.clone()).or_insert(next)
                })
                .collect();
            return Ok(Condition::form_set(forms));
        }

        if let Ok(c) = obj.downcast::<AndCondition>() {
            let conditions: Vec<PyObject> = c.borrow().conditions.iter()
                .map(|o| o.clone_ref(py))
                .collect();
            let conds = conditions.iter()
                .map(|o| self.intern_condition(py, o))
                .collect::<PyResult<Vec<_>>>()?;
            return Ok(Condition::and(conds));
        }

        if let Ok(c) = obj.downcast::<OrCondition>() {
            let conditions: Vec<PyObject> = c.borrow().conditions.iter()
                .map(|o| o.clone_ref(py))
                .collect();
            let conds = conditions.iter()
                .map(|o| self.intern_condition(py, o))
                .collect::<PyResult<Vec<_>>>()?;
            return Ok(Condition::or(conds));
        }

        if let Ok(c) = obj.downcast::<NotCondition>() {
            let inner_obj = c.borrow().condition.clone_ref(py);
            let inner = self.intern_condition(py, &inner_obj)?;
            return Ok(Condition::not(inner));
        }

        Err(PyErr::new::<pyo3::exceptions::PyTypeError, _>(
            format!("unknown condition type: {}", obj.get_type().name()?)
        ))
    }
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// RuleChecker
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

#[pyclass]
pub struct RuleChecker {
    nodes: Vec<RuleNode>,
    transitions: Vec<Transition>,
    optional_closure: Vec<Vec<usize>>,
    eof_closure: Vec<Vec<usize>>,
    bos_epsilon: Vec<usize>,
    form_dict: FxHashMap<String, u32>,
    lemma_dict: FxHashMap<String, u16>,
}

#[pymethods]
impl RuleChecker {
    pub fn check(&self, py: Python, tokens: &Bound<'_, PyList>) -> PyResult<Vec<(u32, u32, u32)>> {
        let enriched = self.enrich_tokens(tokens)?;
        Ok(py.allow_threads(|| self.check_inner(&enriched)))
    }
}

impl RuleChecker {
    fn enrich_tokens(&self, tokens: &Bound<'_, PyList>) -> PyResult<Vec<EnrichedToken>> {
        tokens.iter()
            .map(|t| {
                let form:  String = t.getattr("form")?.extract()?;
                let tag:   String = t.getattr("tag")?.extract()?;
                let start: u32    = t.getattr("start")?.extract()?;
                let end:   u32    = t.getattr("end")?.extract()?;
                let len:   u16    = t.getattr("len")?.extract()?;
                let lemma: String = t.getattr("lemma")?.extract()?;

                let form_idx  = self.form_dict.get(&form).copied().unwrap_or(0);
                let tag_idx   = TAG2IDX.get(tag.as_str()).copied().unwrap_or(0);
                let lemma_idx = self.lemma_dict.get(&lemma).copied().unwrap_or(0);
                let batchim   = Self::get_batchim(&form);

                Ok(EnrichedToken::new(form_idx, tag_idx, start, end, lemma_idx, len, batchim))
            })
            .collect()
    }

    fn get_batchim(form: &str) -> u8 {
        let Some(last) = form.chars().last() else { return 0; };
        let code = last as u32;
        if !(0xAC00..=0xD7A3).contains(&code) {
            return 0;
        }
        ((code - 0xAC00) % 28 + 1) as u8
    }

    fn check_inner(&self, tokens: &[EnrichedToken]) -> Vec<(u32, u32, u32)> {
        if tokens.is_empty() { return Vec::new(); }

        let mut errors: Vec<(u32, u32, u32)> = Vec::new();
        let mut active_cursors:   FxHashMap<usize, (Option<usize>, usize)> = FxHashMap::default();
        let mut next_cursors:     FxHashMap<usize, (Option<usize>, usize)> = FxHashMap::default();
        let mut expanded_cursors: FxHashMap<usize, (Option<usize>, usize)> = FxHashMap::default();
        let mut candidates: Vec<usize> = Vec::new();
        let mut yielded_outputs: FxHashSet<(usize, usize)> = FxHashSet::default();

        for (i, token) in tokens.iter().enumerate() {
            let has_space = i > 0 && token.start > tokens[i - 1].end;

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
            let mut current_step_errors: FxHashMap<(usize, usize), (u32, u32, u32)> = FxHashMap::default();

            for (&node_idx, &(start_idx, end_idx)) in &expanded_cursors {
                let node = &self.nodes[node_idx];

                // 2-A: 출력 수집
                if let Some(start_token_idx) = start_idx {
                    if start_token_idx < i && !yielded_outputs.contains(&(node_idx, start_token_idx)) {
                        yielded_outputs.insert((node_idx, start_token_idx));
                        Self::collect_error(node, tokens, node_idx, start_token_idx, end_idx, &mut current_step_errors);
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
                }
                
                for &trans_idx in &node.fallback_transitions {
                    let trans = &self.transitions[trans_idx];
                    if trans.condition.check_match(token) {
                        candidates.push(trans_idx);
                    }
                }

                // 2-C: spacing 필터 + next_cursors 업데이트
                for &trans_idx in &candidates {
                    let trans = &self.transitions[trans_idx];
                    match trans.spacing_rule {
                        SpacingRule::SPACED   if !has_space => continue,
                        SpacingRule::ATTACHED if  has_space => continue,
                        _ => {}
                    }

                    let target    = trans.target_node;
                    let new_start = if start_idx.is_none() && !trans.is_context { Some(i) } else { start_idx };
                    let new_end   = if !trans.is_context { i } else { end_idx };

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

        let mut final_step_errors: FxHashMap<(usize, usize), (u32, u32, u32)> = FxHashMap::default();
        for (node_idx, (start_idx, end_idx)) in final_expanded {
            let Some(start_token_idx) = start_idx else { continue; };
            if yielded_outputs.contains(&(node_idx, start_token_idx)) { continue; }
            let node = &self.nodes[node_idx];
            Self::collect_error(node, tokens, node_idx, start_token_idx, end_idx, &mut final_step_errors);
        }

        for (_, err) in final_step_errors {
            errors.push(err);
        }

        errors
    }

    fn is_later_start(new: Option<usize>, old: Option<usize>) -> bool {
        match (new, old) {
            (None, _)           => false,
            (Some(_), None)     => true,
            (Some(a), Some(b))  => a > b,
        }
    }

    fn update_shortest_match(
        storage: &mut FxHashMap<(usize, usize), (u32, u32, u32)>,
        node_idx: usize,
        start_token_idx: usize,
        entry: (u32, u32, u32),
    ) {
        let key = (node_idx, start_token_idx);
        match storage.get(&key) {
            None => { storage.insert(key, entry); }
            Some(existing) => {
                let old_len = existing.2 - existing.1;
                let new_len = entry.2 - entry.1;
                if new_len < old_len || (new_len == old_len && entry.1 > existing.1) {
                    storage.insert(key, entry);
                }
            }
        }
    }

    fn collect_error(
        node: &RuleNode,
        tokens: &[EnrichedToken],
        node_idx: usize,
        start_token_idx: usize,
        end_idx: usize,
        storage: &mut FxHashMap<(usize, usize), (u32, u32, u32)>,
    ) {
        let Some(match_id) = node.match_id else { return; };
        let entry = (
            match_id,
            start_token_idx as u32,
            end_idx as u32,
        );
        Self::update_shortest_match(storage, node_idx, start_token_idx, entry);
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