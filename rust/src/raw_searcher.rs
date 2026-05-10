use std::collections::VecDeque;
use rustc_hash::{FxHashMap, FxHashSet};
use pyo3::prelude::*;

struct TrieNode {
    children: FxHashMap<char, usize>,
    output: FxHashSet<(String, usize, String, String)>,
    fail: usize,
}

impl TrieNode {
    fn new() -> Self {
        TrieNode {
            children: FxHashMap::default(),
            output: FxHashSet::default(),
            fail: 0,
        }
    }
}

#[pyclass(subclass)]
pub struct RustRawStringSearcher {
    nodes: Vec<TrieNode>,
    built: bool,
}

#[pymethods]
impl RustRawStringSearcher {
    #[new]
    pub fn new() -> Self {
        RustRawStringSearcher {
            nodes: vec![TrieNode::new()],
            built: false,
        }
    }

    pub fn add_word(&mut self, word: String, msg: String, error_type: String, rule_id: String) -> PyResult<()> {
        if self.built {
            return Err(pyo3::exceptions::PyRuntimeError::new_err(
                "cannot add words after build."
            ));
        }

        let mut curr_node: usize = 0;
        let char_count = word.chars().count();

        for ch in word.chars() {
            if !self.nodes[curr_node].children.contains_key(&ch) {
                let new_index = self.nodes.len();
                self.nodes.push(TrieNode::new());
                self.nodes[curr_node].children.insert(ch, new_index);
            }
            curr_node = self.nodes[curr_node].children[&ch];
        }
        self.nodes[curr_node].output.insert((msg, char_count, error_type, rule_id));

        Ok(())
    }

    pub fn build(&mut self) {
        let mut queue: VecDeque<usize> = VecDeque::new();
        let root_children: Vec<usize> = self.nodes[0].children.values().copied().collect();

        for child_idx in root_children {
            self.nodes[child_idx].fail = 0;
            queue.push_back(child_idx);
        }

        while let Some(node_idx) = queue.pop_front() {
            let children: Vec<(char, usize)> = self.nodes[node_idx].children.iter().map(|(&c, &idx)| (c, idx)).collect();
            for (ch, child_node) in children {
                let mut dest = self.nodes[node_idx].fail;

                while dest != 0 && !self.nodes[dest].children.contains_key(&ch) {
                    dest = self.nodes[dest].fail;
                }

                self.nodes[child_node].fail = if self.nodes[dest].children.contains_key(&ch) {
                    let candidate = self.nodes[dest].children[&ch];
                    if candidate == child_node { 0 } else { candidate }
                } else {
                    0
                };

                let fail_idx = self.nodes[child_node].fail;
                if !self.nodes[fail_idx].output.is_empty() {
                    let fail_output: FxHashSet<_> = self.nodes[fail_idx].output.clone();
                    self.nodes[child_node].output.extend(fail_output);
                }

                queue.push_back(child_node);
            }
        }

        self.built = true;
    }

    pub fn search_raw(&mut self, word: &str) -> PyResult<Vec<(String, String, usize, usize, String)>> {
        if self.nodes[0].children.is_empty() {
            return Err(pyo3::exceptions::PyValueError::new_err(
                "You must have at least one word to search."
            ));
        }

        if !self.built {
            self.build();
        }

        let mut current = 0;
        let mut result = Vec::new();

        for (idx, ch) in word.chars().enumerate() {
            while current != 0 && !self.nodes[current].children.contains_key(&ch) {
                current = self.nodes[current].fail;
            }

            if let Some(&next) = self.nodes[current].children.get(&ch) {
                current = next;
                for (msg, len, error_type, rule_id) in self.nodes[current].output.iter() {
                    result.push((error_type.clone(), msg.clone(), idx + 1 - len, idx + 1, rule_id.clone()));
                }
            }
        }

        Ok(result)
    }
}