from __future__ import annotations
from typing import Iterator

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


def _message_to_rust(msg: CompiledMessage):
    if all(isinstance(p, str) for p in msg._parts):
        return "".join(msg._parts)  # type: ignore[arg-type]
    def render(tokens, start):
        return msg.render(tokens[start:])
    return render


class SpellChecker:
    def __init__(self, debug: bool = False):
        self._builder: RuleCheckerBuilder | None = RuleCheckerBuilder(debug)
        self._checker: RuleChecker | None = None
        self._has_rules: bool = False
        self._debug: bool = debug

    def _add_rule(self, rules: KoSpellRules) -> None:
        if self._builder is None:
            raise RuntimeError("You cannot add rules after calling 'check' function.")

        steps, msg, error_type, rule_id = rules
        if not steps:
            return

        rust_steps = [
            (_to_rust_condition(cond), spacing.value, is_optional, is_context)
            for cond, spacing, is_optional, is_context in steps
        ]

        self._builder.add_rule(
            steps=rust_steps,
            message=_message_to_rust(msg),
            error_type=error_type.value,
            rule_id=rule_id,
        )
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
            self._checker = self._builder.build()
            self._builder = None

        rust_errors = self._checker.check(tokens)
        return (
            SpellError(
                error_type=SpellErrorType(int(e.error_type)),
                error_message=e.error_message,
                start_index=e.start_index,
                end_index=e.end_index,
                rule_id=e.rule_id,
                debug_path=e.debug_path,
            )
            for e in rust_errors
        )