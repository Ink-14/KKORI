from __future__ import annotations
from dataclasses import dataclass
from collections import deque
from typing import Iterator
from abc import ABC, abstractmethod

from korean_spell_checker.models.interface import KoToken, SpellError, SpellErrorType, TAG2IDX
from korean_spell_checker.models.spell_checker_classes import SpacingRule, Condition, TagCondition, FormCondition, TagAndFormCondition, NotCondition, BatchimCondition, AnyBatchimCondition, AndCondition, OrCondition, TagSetCondition, FormSetCondition
from korean_spell_checker.utils.hangul import get_compatible_batchim_int, BATCHIM_DICT
from korean_spell_checker.configs.spell_checker_config_builder import KoSpellRules, CompiledMessage

@dataclass(slots=True)
class _EnrichedToken:
    form: int
    tag: int
    form_tag: int
    start: int
    end: int
    len: int
    lemma: str
    batchim: int

@dataclass(frozen=True, slots=True)
class _Transition:
    condition: Condition | InternedCondition
    target_node: _RuleNode
    spacing_rule: SpacingRule = SpacingRule.ANY
    is_optional: bool = False
    is_context: bool = False

# rust 포팅 시 enum이 될 부분이므로 엔진에서 정의
@dataclass(frozen=True, slots=True)
class InternedCondition(ABC):
    @abstractmethod
    def match(self, token: _EnrichedToken) -> bool:
        """상속받은 클래스에서 구현해야 하는 추상 메서드. 조건 만족 시 True를 반환하도록 구현해야 함."""
        raise NotImplementedError

@dataclass(frozen=True, slots=True)
class InternedBatchimCondition(InternedCondition):
    batchim: int
    def match(self, token: _EnrichedToken) -> bool:
        return token.batchim == self.batchim

@dataclass(frozen=True, slots=True)
class InternedAnyBatchimCondition(InternedCondition):
    def match(self, token: _EnrichedToken) -> bool:
        return token.batchim > 1  # 0 = UNK, 1 = 받침 없음

@dataclass(frozen=True, slots=True)
class InternedTagCondition(InternedCondition):
    tag: int
    def match(self, token: _EnrichedToken) -> bool:
        return token.tag == self.tag

@dataclass(frozen=True, slots=True)
class InternedFormCondition(InternedCondition):
    form: int
    def match(self, token: _EnrichedToken) -> bool:
        return token.form == self.form

@dataclass(frozen=True, slots=True)
class InternedTagAndFormCondition(InternedCondition):
    form_tag: int
    
    def match(self, token: _EnrichedToken) -> bool:
        return token.form_tag == self.form_tag

@dataclass(frozen=True, slots=True)
class InternedFormSetCondition(InternedCondition):
    forms: frozenset[int]
    def match(self, token: _EnrichedToken) -> bool:
        return token.form in self.forms

@dataclass(frozen=True, slots=True)
class InternedTagSetCondition(InternedCondition):
    tags: frozenset[int]
    def match(self, token: _EnrichedToken) -> bool:
        return token.tag in self.tags


class _RuleNode:
    __slots__ = (
        'tag_transitions', 'form_transitions', 'form_and_tag_transitions', 'batchim_transitions', 'any_batchim_transitions', 'fallback_transitions',
        'optional_closure', 'eof_closure', 'output_message', 'output_path', 'error_type', 'rule_id',
    )

    def __init__(self):
        self.tag_transitions: dict[int, list[_Transition]] = {}
        self.form_transitions: dict[int, list[_Transition]] = {}
        self.form_and_tag_transitions: dict[int, list[_Transition]] = {}
        self.batchim_transitions: list[list[_Transition] | None] | None = None
        self.any_batchim_transitions: list[_Transition] = []
        self.fallback_transitions: list[_Transition] = []

        self.optional_closure: frozenset[_RuleNode] = frozenset()
        self.eof_closure: frozenset[_RuleNode] = frozenset()

        self.output_message: CompiledMessage | None = None
        self.error_type: SpellErrorType = SpellErrorType.NOT_SET
        self.output_path: str | None = None
        self.rule_id: str = ""

    def __repr__(self):
        n = sum(1 for _ in self._iter_all_transitions())
        out = "CompiledMessage" if self.output_message else "None"
        return f"_RuleNode(transitions={n}, output={out})"

    def _iter_all_transitions(self) -> Iterator[_Transition]:
        """빌드/freeze 단계에서만 사용하는 모든 전이 순회 헬퍼."""
        yield from self.fallback_transitions
        yield from self.any_batchim_transitions
        for lst in self.tag_transitions.values():
            yield from lst
        for lst in self.form_transitions.values():
            yield from lst
        for lst in self.form_and_tag_transitions.values():
            yield from lst
        if self.batchim_transitions is not None:
            for lst in self.batchim_transitions:
                if lst is not None:
                    yield from lst

    def get_or_create_next_node(self, condition: Condition | InternedCondition, spacing_rule: SpacingRule, is_optional: bool, is_context: bool) -> _RuleNode:
        """조건에 맞는 간선을 찾거나 새로 생성하여 다음 노드를 반환하는 함수."""
        existing_node = self._find_transition(condition, spacing_rule, is_optional, is_context)
        if existing_node:
            return existing_node

        next_node = _RuleNode()
        new_trans = _Transition(condition=condition, target_node=next_node, spacing_rule=spacing_rule, is_optional=is_optional, is_context=is_context)
        self._add_transition_to_node(condition, new_trans)
        return next_node

    def _find_transition(self, cond: Condition | InternedCondition, spacing: SpacingRule, optional: bool, context: bool) -> _RuleNode | None:
        target_list = []

        if isinstance(cond, InternedTagAndFormCondition):
            target_list = self.form_and_tag_transitions.get(cond.form_tag, [])
        elif isinstance(cond, InternedTagCondition):
            target_list = self.tag_transitions.get(cond.tag, [])
        elif isinstance(cond, InternedFormCondition):
            target_list = self.form_transitions.get(cond.form, [])
        elif isinstance(cond, InternedBatchimCondition):
            if self.batchim_transitions is None:
                return None
            if self.batchim_transitions[cond.batchim] is None:  # type: ignore
                return None
            target_list = self.batchim_transitions[cond.batchim]  # type: ignore
        elif isinstance(cond, InternedAnyBatchimCondition):
            target_list = self.any_batchim_transitions
        else:
            for t in self.fallback_transitions:
                if t.condition == cond and t.spacing_rule == spacing and t.is_optional == optional and t.is_context == context:
                    return t.target_node
            return None

        for t in target_list:  # type: ignore
            if t.spacing_rule == spacing and t.is_optional == optional and t.is_context == context:
                return t.target_node

        return None

    def _add_transition_to_node(self, cond: Condition | InternedCondition, trans: _Transition):
        if isinstance(cond, InternedTagAndFormCondition):
            self.form_and_tag_transitions.setdefault(cond.form_tag, []).append(trans)
        elif isinstance(cond, InternedTagCondition):
            self.tag_transitions.setdefault(cond.tag, []).append(trans)
        elif isinstance(cond, InternedFormCondition):
            self.form_transitions.setdefault(cond.form, []).append(trans)
        elif isinstance(cond, InternedBatchimCondition):
            if self.batchim_transitions is None:
                self.batchim_transitions = [None] * 29  # type: ignore
            if self.batchim_transitions[cond.batchim] is None:  # type: ignore
                self.batchim_transitions[cond.batchim] = []  # type: ignore
            self.batchim_transitions[cond.batchim].append(trans)  # type: ignore
        elif isinstance(cond, InternedAnyBatchimCondition):
            self.any_batchim_transitions.append(trans)
        else:
            self.fallback_transitions.append(trans)

class SpellChecker:
    def __init__(self, debug: bool = False):
        self._root = _RuleNode()
        self._is_frozen: bool = False
        self._debug: bool = debug
        self._has_rules: bool = False
        self._bos_epsilon: dict[_RuleNode, tuple[int, int]] | None = None
        self._form_dict: dict[str, int] = {"__UNK__": 0}

    def _interning(self, cond: Condition) -> InternedCondition | Condition:
        if isinstance(cond, BatchimCondition):
            return InternedBatchimCondition(BATCHIM_DICT[cond.batchim])
        elif isinstance(cond, AnyBatchimCondition):
            return InternedAnyBatchimCondition()
        elif isinstance(cond, TagAndFormCondition):
            form_idx = self._form_dict.setdefault(cond.form, len(self._form_dict))
            tag_idx = TAG2IDX[cond.tag]
            assert tag_idx < 128, f"tag overflow: {tag_idx}"
            return InternedTagAndFormCondition(form_tag=(form_idx << 7) | tag_idx)
        elif isinstance(cond, FormCondition):
            return InternedFormCondition(self._form_dict.setdefault(cond.form, len(self._form_dict)))
        elif isinstance(cond, TagCondition):
            return InternedTagCondition(TAG2IDX[cond.tag])
        elif isinstance(cond, TagSetCondition):
            return InternedTagSetCondition(frozenset(TAG2IDX[tag] for tag in cond.tags))
        elif isinstance(cond, FormSetCondition):
            return InternedFormSetCondition(frozenset(self._form_dict.setdefault(form, len(self._form_dict)) for form in cond.forms))
        elif isinstance(cond, AndCondition):
            return AndCondition(conditions=tuple(self._interning(c) for c in cond.conditions))  # type: ignore
        elif isinstance(cond, OrCondition):
            return OrCondition(conditions=tuple(self._interning(c) for c in cond.conditions))  # type: ignore
        elif isinstance(cond, NotCondition):
            return NotCondition(condition=self._interning(cond.condition))  # type: ignore
        return cond

    def _add_rule(self, rules: KoSpellRules) -> None:
        if self._is_frozen:
            raise RuntimeError("You cannot add rules after calling 'check' function.")

        current = self._root
        path = []
        conditions, msg, error_type, rule_id = rules

        if len(conditions) == 0:
            return

        for cond, spacing, optional, context in conditions:
            if self._debug:
                path.append(f"{cond}, {spacing}, {optional}, {context}")
            cond = self._interning(cond)
            current = current.get_or_create_next_node(condition=cond, spacing_rule=spacing, is_optional=optional, is_context=context)

        current.output_message = msg
        current.error_type = error_type
        current.rule_id = rule_id

        if self._debug:
            current.output_path = "  →  ".join(path)

        self._has_rules = True

    def add_rule_from_list(self, rules: list[KoSpellRules]) -> None:
        """KoSpellRules가 담긴 list를 받아 규칙을 추가하는 함수."""
        for rule in rules:
            self._add_rule(rule)

    def check(self, tokens: list[KoToken]) -> Iterator[SpellError]:
        """토큰을 검사하는 함수.

        Args:
            tokens: KoToken의 list.

        Raises:
            ValueError: 아무 규칙도 추가하지 않고 호출 시 ValueError 발생.

        Yields:
            SpellError: 발견된 맞춤법 오류 정보를 순차적으로 반환.
        """
        if not self._has_rules:
            raise ValueError("You must have at least one rule to check spelling.")

        if not self._is_frozen:
            self._freeze()

        return self._check_impl(tokens)

    def _freeze(self) -> None:
        """closure 계산 및 캐싱."""
        # 1) root에서 도달 가능한 모든 노드 수집
        all_nodes: list[_RuleNode] = []
        seen: set[int] = {id(self._root)}
        bfs: deque[_RuleNode] = deque([self._root])
        while bfs:
            node = bfs.popleft()
            all_nodes.append(node)
            for trans in node._iter_all_transitions():
                t = trans.target_node
                if id(t) not in seen:
                    seen.add(id(t))
                    bfs.append(t)

        # 2) 각 노드의 optional closure
        for node in all_nodes:
            closure: set[_RuleNode] = {node}
            q: deque[_RuleNode] = deque([node])
            while q:
                cur = q.popleft()
                for trans in cur._iter_all_transitions():
                    if trans.is_optional and trans.target_node not in closure:
                        closure.add(trans.target_node)
                        q.append(trans.target_node)
            node.optional_closure = frozenset(closure)

        # 3) 각 노드의 EOF closure 계산
        #    (optional or NotCondition + ANY + context 전이를 엡실론으로 간주)
        for node in all_nodes:
            closure = {node}
            q = deque([node])
            while q:
                cur = q.popleft()
                for trans in cur._iter_all_transitions():
                    is_not_any = (
                        isinstance(trans.condition, NotCondition)
                        and trans.spacing_rule == SpacingRule.ANY
                        and trans.is_context
                    )
                    if (trans.is_optional or is_not_any) and trans.target_node not in closure:
                        closure.add(trans.target_node)
                        q.append(trans.target_node)
            node.eof_closure = frozenset(closure)

        # 4) BOS epsilon 캐시 계산
        self._bos_epsilon = self._compute_bos_epsilon()

        self._is_frozen = True

    def _check_impl(self, tokens: list[KoToken]) -> Iterator[SpellError]:
        """NFA 시뮬레이션 기반 토큰 검사.

        각 토큰마다 아래 4단계를 반복:
        1) root에서 새 커서 시작
        2) optional 전이로 도달 가능한 노드 확장 (epsilon closure, 사전 계산된 캐시 사용)
           - i==0이면 BOS epsilon 사용 (NOT 전이까지 엡실론 처리)
        3) 출력 가능한 노드에서 에러 수집
        4) 현재 토큰과 매칭되는 전이를 따라 커서 전진

        동일 노드에 여러 커서가 도달하면 가장 늦은 시작점만 유지 (최단 매치 우선).
        루프 종료 후 남은 커서에 대해 EOF closure로 확장해 출력 수집.
        """
        enriched_tokens = [
            _EnrichedToken(
                form=(form_idx := self._form_dict.get(t.form, 0)), tag=(tag_idx := TAG2IDX[t.tag]), form_tag=(form_idx << 7) | tag_idx,
                start=t.start, end=t.end, len=t.len, lemma=t.lemma, batchim=(get_compatible_batchim_int(t.form[-1]))
            )
            for t in tokens
        ]

        active_cursors: dict[_RuleNode, tuple[int, int]] = {}
        next_cursors: dict[_RuleNode, tuple[int, int]] = {}
        expanded_cursors: dict[_RuleNode, tuple[int, int]] = {}

        candidates: list[_Transition] = []
        yielded_outputs: set[tuple[_RuleNode, int]] = set()
        NOT_STARTED = -1

        for i, token in enumerate(enriched_tokens):
            has_space = (token.start - tokens[i-1].end > 0) if i > 0 else False

            expanded_cursors.clear()

            # ── Phase 1: epsilon closure 확장 ──
            if i == 0:
                expanded_cursors.update(self._bos_epsilon)  # type: ignore
            else:
                active_cursors[self._root] = (NOT_STARTED, i)

                for node, idxs in active_cursors.items():
                    start_idx, end_idx = idxs

                    if node not in expanded_cursors or start_idx > expanded_cursors[node][0]:
                        expanded_cursors[node] = (start_idx, end_idx)

                    for closure_node in node.optional_closure:
                        if closure_node not in expanded_cursors or start_idx > expanded_cursors[closure_node][0]:
                            expanded_cursors[closure_node] = (start_idx, end_idx)

            # ── Phase 2: 출력 수집 & 전이 탐색 ──
            next_cursors.clear()
            current_step_errors: dict[str, tuple[SpellErrorType, int, int, str, str | None]] = {}

            for node, idxs in expanded_cursors.items():
                start_idx, end_idx = idxs

                if node.output_message and start_idx < i and (node, start_idx) not in yielded_outputs:
                    yielded_outputs.add((node, start_idx))
                    self._update_shortest_match(
                        current_step_errors,
                        node.output_message.render(tokens[start_idx:end_idx+1]),
                        node.error_type,
                        tokens[start_idx].start,
                        tokens[end_idx].end,
                        node.rule_id,
                        node.output_path
                    )

                candidates.clear()

                if tt := node.tag_transitions.get(token.tag):
                    candidates.extend(tt)
                if token.form > 0:
                    if ft2 := node.form_transitions.get(token.form):
                        candidates.extend(ft2)
                    if ftt := node.form_and_tag_transitions.get(token.form_tag):
                        candidates.extend(ftt)
                if token.batchim > 0:
                    if node.batchim_transitions is not None and node.batchim_transitions[token.batchim] is not None:
                        candidates.extend(node.batchim_transitions[token.batchim])  # type: ignore
                if token.batchim > 1:
                    candidates.extend(node.any_batchim_transitions)

                for t in node.fallback_transitions:
                    if t.condition.match(token):
                        candidates.append(t)

                for trans in candidates:
                    if trans.spacing_rule == SpacingRule.SPACED and not has_space:
                        continue
                    elif trans.spacing_rule == SpacingRule.ATTACHED and has_space:
                        continue

                    target = trans.target_node

                    new_start = i if (start_idx == NOT_STARTED and not trans.is_context) else start_idx
                    new_end   = i if not trans.is_context else end_idx
                    if target not in next_cursors or new_start > next_cursors[target][0]:
                        next_cursors[target] = (new_start, new_end)

            # ── Phase 3: 에러 yield & 커서 스왑 ──
            for msg, (err_type, start, end, rule_id, output_path) in current_step_errors.items():
                yield SpellError(
                    error_type=err_type,
                    error_message=msg,
                    start_index=start,
                    end_index=end,  
                    rule_id=rule_id,
                    debug_path=output_path
                )

            active_cursors, next_cursors = next_cursors, active_cursors

        # ── EOF epsilon ──
        if tokens:
            final_step_errors: dict[str, tuple[SpellErrorType, int, int, str, str | None]] = {}
            final_expanded: dict[_RuleNode, tuple[int, int]] = {}

            for node, idxs in active_cursors.items():
                start_idx, end_idx = idxs
                for closure_node in node.eof_closure:
                    if closure_node not in final_expanded or start_idx > final_expanded[closure_node][0]:
                        final_expanded[closure_node] = (start_idx, end_idx)

            for node, idxs in final_expanded.items():
                start_idx, end_idx = idxs
                if node.output_message and (node, start_idx) not in yielded_outputs:
                    self._update_shortest_match(
                        storage=final_step_errors,
                        msg=node.output_message.render(tokens[start_idx:end_idx+1]),
                        error_type=node.error_type,
                        start=tokens[start_idx].start,
                        end=tokens[end_idx].end,
                        rule_id=node.rule_id,
                        output_path=node.output_path
                    )

            for msg, (err_type, start, end, rule_id, output_path) in final_step_errors.items():
                yield SpellError(
                    error_type=err_type,
                    error_message=msg,
                    start_index=start,
                    end_index=end,
                    rule_id=rule_id,
                    debug_path=output_path
                )

    def _update_shortest_match(self, storage: dict[str, tuple[SpellErrorType, int, int, str, str | None]], msg: str, error_type: SpellErrorType, start: int, end: int, rule_id: str, output_path: str | None) -> None:
        if msg not in storage:
            storage[msg] = (error_type, start, end, rule_id, output_path)
        else:
            _, old_start, old_end, _, _ = storage[msg]
            old_length = old_end - old_start
            new_length = end - start
            # 더 짧은 것 선택, 길이 같으면 더 뒤에 있는 것
            if new_length < old_length or (new_length == old_length and start > old_start):
                storage[msg] = (error_type, start, end, rule_id, output_path)

    def _compute_bos_epsilon(self) -> dict[_RuleNode, tuple[int, int]]:
        """BOS epsilon 전이 결과를 미리 계산해 캐싱."""
        NOT_STARTED = -1
        i = 0

        expanded: dict[_RuleNode, tuple[int, int]] = {}

        # ── Phase 1 상당: root + root의 optional closure (자기 자신 포함) ──
        for node in self._root.optional_closure:
            expanded[node] = (NOT_STARTED, i)

        # ── BOS NOT/context 전이 확장 ──
        bos_queue = deque(expanded.items())
        while bos_queue:
            current_node, idxs = bos_queue.popleft()
            start_idx, end_idx = idxs

            for trans in current_node.fallback_transitions:
                if not (isinstance(trans.condition, NotCondition) and trans.spacing_rule == SpacingRule.ANY and trans.is_context):
                    continue

                target = trans.target_node
                new_start = i if (start_idx == NOT_STARTED and not trans.is_context) else start_idx
                new_end = i if not trans.is_context else end_idx

                if target not in expanded or new_start > expanded[target][0]:
                    expanded[target] = (new_start, new_end)
                    bos_queue.append((target, (new_start, new_end)))
                    for opt_node in target.optional_closure:
                        if opt_node not in expanded or new_start > expanded[opt_node][0]:
                            expanded[opt_node] = (new_start, new_end)
                            bos_queue.append((opt_node, (new_start, new_end)))

        return expanded