from __future__ import annotations
import heapq
from typing import Iterator
from dataclasses import dataclass

from _core import (
    RuleCheckerBuilder, RuleChecker,
    TagCondition as RustTagCondition,
    FormCondition as RustFormCondition,
    TagAndFormCondition as RustTagAndFormCondition,
    LemmaCondition as RustLemmaCondition,
    AnyCondition as RustAnyCondition,
    AnyBatchimCondition as RustAnyBatchimCondition,
    BatchimCondition as RustBatchimCondition,
    LengthCondition as RustLengthCondition,
    LengthLongerCondition as RustLengthLongerCondition,
    FirstTokenCondition as RustFirstTokenCondition,
    TagSetCondition as RustTagSetCondition,
    FormSetCondition as RustFormSetCondition,
    AndCondition as RustAndCondition,
    OrCondition as RustOrCondition,
    NotCondition as RustNotCondition,
    RuleCheckerStats
)
from src.models.interface import KoToken, SpellError, SpellErrorType, DetailedMessage
from src.models.spell_checker_classes import (
    Condition,
    TagCondition, FormCondition, TagAndFormCondition, LemmaCondition,
    AnyCondition, AnyBatchimCondition, BatchimCondition,
    LengthCondition, LengthLongerCondition, FirstTokenCondition,
    TagSetCondition, FormSetCondition,
    AndCondition, OrCondition, NotCondition,
)
from src.engines.configs.rule_builder import KoSpellRules, CompiledMessage

@dataclass(frozen=True, slots=True)
class RuleMetaData:
    error_type: SpellErrorType
    msg: CompiledMessage
    rule_id: str
    detail: DetailedMessage
    priority: int
    debug_path: str | None = None

def _to_rust_condition(cond: Condition) -> object:
    if isinstance(cond, TagAndFormCondition):
        return RustTagAndFormCondition(form=cond.form, tag=cond.tag)
    if isinstance(cond, TagCondition):
        return RustTagCondition(tag=cond.tag)
    if isinstance(cond, FormCondition):
        return RustFormCondition(form=cond.form)
    if isinstance(cond, LemmaCondition):
        return RustLemmaCondition(lemma=cond.lemma)
    if isinstance(cond, AnyBatchimCondition):
        return RustAnyBatchimCondition()
    if isinstance(cond, BatchimCondition):
        return RustBatchimCondition(batchim=cond.batchim)
    if isinstance(cond, AnyCondition):
        return RustAnyCondition()
    if isinstance(cond, LengthCondition):
        return RustLengthCondition(length=cond.length)
    if isinstance(cond, LengthLongerCondition):
        return RustLengthLongerCondition(length=cond.length)
    if isinstance(cond, FirstTokenCondition):
        return RustFirstTokenCondition()
    if isinstance(cond, TagSetCondition):
        return RustTagSetCondition(tags=list(cond.tags))
    if isinstance(cond, FormSetCondition):
        return RustFormSetCondition(forms=list(cond.forms))
    if isinstance(cond, AndCondition):
        return RustAndCondition(conditions=[_to_rust_condition(c) for c in cond.conditions])
    if isinstance(cond, OrCondition):
        return RustOrCondition(conditions=[_to_rust_condition(c) for c in cond.conditions])
    if isinstance(cond, NotCondition):
        return RustNotCondition(condition=_to_rust_condition(cond.condition))
    raise TypeError(f"Unknown condition type: {type(cond)}")

class SpellChecker:
    def __init__(self, debug: bool = False):
        self._builder: RuleCheckerBuilder | None = RuleCheckerBuilder()
        self._checker: RuleChecker | None = None
        self._has_rules: bool = False
        self._debug: bool = debug

        self._registry: list[RuleMetaData] = []
        self.total_steps: int = 0

    def detect_rule_id_dup(self) -> list[str]:
        rule_id_set = set()
        rule_id_set.add(self._registry[0].rule_id)
        result = []

        for i in range(1, len(self._registry)):
            current = self._registry[i]
            before = self._registry[i-1]

            if current.rule_id == before.rule_id: # todo - suffix 공유해서 최적화하면 삭제할 부분
                continue

            if current.rule_id == "":
                continue
            elif current.rule_id in rule_id_set:
                result.append(current.rule_id)
            else:
                rule_id_set.add(current.rule_id)

        return result

    def _add_rule(self, rules: KoSpellRules) -> None:
        if self._builder is None:
            raise RuntimeError("You cannot add rules after calling 'check' function.")

        steps, msg, error_type, rule_id, detail, priority = rules
        if not steps:
            return

        rust_steps = []
        path = []

        for cond, spacing, is_optional, is_context in steps:
            if self._debug:
                path.append(f"{cond}, {spacing}, {is_optional}, {is_context}")
                self.total_steps += 1
            rust_steps.append(
                (_to_rust_condition(cond), spacing.value, is_optional, is_context)
            )

        uid = len(self._registry)
        debug_path = "  →  ".join(path) if self._debug else None
        self._registry.append(RuleMetaData(error_type, msg, rule_id, detail, priority, debug_path))

        self._builder.add_rule(steps=rust_steps, match_id=uid)
        self._has_rules = True

    def add_rule_from_list(self, rules: list[KoSpellRules]) -> None:
        """KoSpellRules가 담긴 list를 받아 규칙을 추가하는 함수."""
        for rule in rules:
            self._add_rule(rule)

    def _ensure_built(self) -> None:
        if self._checker is None:
            self._checker = self._builder.build()  # type: ignore
            self._builder = None

    def _make_spell_error(
        self,
        tokens: list[KoToken],
        match_id: int,
        start_index: int,
        end_index: int,
    ) -> tuple[SpellError, tuple[int, int, str]]:
        meta = self._registry[match_id]

        sliced_tokens = tokens[start_index : end_index + 1]
        raw_message = meta.msg.render(sliced_tokens)

        error_message = (
            f"{match_id}: {raw_message}"
            if self._debug
            else raw_message
        )

        start = tokens[start_index].start
        end = tokens[end_index].end

        error = SpellError(
            error_type=meta.error_type,
            error_message=error_message,
            start_index=start,
            end_index=end,
            rule_id=meta.rule_id,
            detailed=meta.detail,
            priority=meta.priority,
            debug_path=meta.debug_path,
        )
        
        dedup_key = (start, end, raw_message)

        return error, dedup_key

    def _deduped_errors(
        self,
        tokens: list[KoToken],
        rust_errors,
    ) -> list[SpellError]:
        seen: set[tuple[int, int, str]] = set()
        result: list[SpellError] = []

        for match_id, start_index, end_index in rust_errors:
            error, key = self._make_spell_error(
                tokens,
                match_id,
                start_index,
                end_index,
            )

            if key in seen:
                continue

            seen.add(key)
            result.append(error)

        return result

    @staticmethod
    def _suppress_overlaps(errors: list[SpellError]) -> list[SpellError]:
        n = len(errors)
        priorities = [e.priority for e in errors]
        is_suppress_all_type = [e.error_type == SpellErrorType.SUPPRESS_ALL for e in errors]
        suppressed = list(is_suppress_all_type)

        order = sorted(range(n), key=lambda i: errors[i].start_index)
        active: list[tuple[int, int]] = []

        for i in order:
            start_i = errors[i].start_index

            while active and active[0][0] <= start_i:
                heapq.heappop(active)

            for _, j in active:
                if is_suppress_all_type[i] or is_suppress_all_type[j]:
                    suppressed[i] = True
                    suppressed[j] = True
                elif priorities[i] < priorities[j]:
                    suppressed[j] = True
                elif priorities[j] < priorities[i]:
                    suppressed[i] = True

            heapq.heappush(active, (errors[i].end_index, i))

        return [e for e, is_suppressed in zip(errors, suppressed) if not is_suppressed]

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

        self._ensure_built()
        assert self._checker is not None

        rust_errors = self._checker.check(tokens)

        errors = self._deduped_errors(tokens, rust_errors)
        yield from self._suppress_overlaps(errors)

    def check_batch(self, batch: list[list[KoToken]]) -> list[list[SpellError]]:
        """병렬 검사용 함수."""
        if not self._has_rules:
            raise ValueError("You must have at least one rule to check spelling.")

        self._ensure_built()
        assert self._checker is not None

        tuple_batch = [
            [(t.form, t.tag, t.start, t.end, t.len, t.lemma) for t in tokens]
            for tokens in batch
        ]

        rust_batch = self._checker.check_batch_tuples(tuple_batch)
        result = []

        for tokens, rust_errors in zip(batch, rust_batch):
            errors = self._deduped_errors(tokens, rust_errors)
            result.append(self._suppress_overlaps(errors))

        return result
    
    def stats(self) -> RuleCheckerStats:
        """
        디버깅용.

        Returns:
            RuleCheckerStats: 체커의 노드 분포.
        """
        self._ensure_built()
        assert self._checker is not None
        return self._checker.stats()