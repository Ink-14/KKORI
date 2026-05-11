from __future__ import annotations
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
    NoBatchimCondition as RustNoBatchimCondition,
    BatchimCondition as RustBatchimCondition,
    LengthCondition as RustLengthCondition,
    FirstTokenCondition as RustFirstTokenCondition,
    TagSetCondition as RustTagSetCondition,
    FormSetCondition as RustFormSetCondition,
    AndCondition as RustAndCondition,
    OrCondition as RustOrCondition,
    NotCondition as RustNotCondition,
)
from korean_spell_checker.models.interface import KoToken, SpellError, SpellErrorType
from korean_spell_checker.models.spell_checker_classes import (
    SpacingRule, Condition,
    TagCondition, FormCondition, TagAndFormCondition, LemmaCondition,
    AnyCondition, AnyBatchimCondition, BatchimCondition,
    LengthCondition, FirstTokenCondition,
    TagSetCondition, FormSetCondition,
    AndCondition, OrCondition, NotCondition,
)
from korean_spell_checker.configs.spell_checker_config_builder import KoSpellRules, CompiledMessage

@dataclass(frozen=True, slots=True)
class RuleMetaData:
    error_type: SpellErrorType
    msg: CompiledMessage
    rule_id: str
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

    def _add_rule(self, rules: KoSpellRules) -> None:
        if self._builder is None:
            raise RuntimeError("You cannot add rules after calling 'check' function.")

        steps, msg, error_type, rule_id = rules
        if not steps:
            return

        rust_steps = []
        path = []
        
        for cond, spacing, is_optional, is_context in steps:
            if self._debug:
                path.append(f"{cond}, {spacing}, {is_optional}, {is_context}")
            rust_steps.append(
                (_to_rust_condition(cond), spacing.value, is_optional, is_context)
            )

        uid = len(self._registry)
        debug_path = "  →  ".join(path) if self._debug else None
        self._registry.append(RuleMetaData(error_type, msg, rule_id, debug_path))

        self._builder.add_rule(steps=rust_steps, match_id=uid)
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

        if self._checker is None:
            self._checker = self._builder.build() # type: ignore
            self._builder = None

        rust_errors = self._checker.check(tokens)
        for match_id, start_index, end_index in rust_errors:
            meta = self._registry[match_id]
            yield SpellError(
                error_type=meta.error_type,
                error_message=meta.msg.render(tokens[start_index : end_index + 1]),
                start_index=tokens[start_index].start,
                end_index=tokens[end_index].end,
                rule_id=meta.rule_id,
                debug_path=meta.debug_path,
            )