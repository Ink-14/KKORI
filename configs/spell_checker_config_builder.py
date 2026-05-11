from typing import TypeAlias, Callable
from itertools import product
from dataclasses import dataclass
import warnings

from korean_spell_checker.models.spell_checker_classes import *
from korean_spell_checker.models.interface import SpellErrorType, Tag, RuleId
from korean_spell_checker.configs.spell_checker_config_builder_parser import MessageTokenizer, MessageParser, TagNode, TextNode, MethodNode, QuotedNode, MESSAGE_METHODS

ErrorMessage: TypeAlias = str
RuleSteps: TypeAlias = list[tuple[Condition, SpacingRule, bool, bool]]
KoSpellRules: TypeAlias = tuple[RuleSteps, "CompiledMessage", SpellErrorType, RuleId]
AndParam: TypeAlias = "Condition | _TagSet | _FormSet"
MessagePart: TypeAlias = str | Callable[[list], str]

tokenizer = MessageTokenizer()
parser = MessageParser()

class _DynamicPart:
    __slots__ = ('_fn', '_desc')

    def __init__(self, fn: Callable[[list], str], desc: str):
        self._fn = fn
        self._desc = desc

    def __call__(self, tokens: list) -> str:
        return self._fn(tokens)

    def __repr__(self) -> str:
        return f"<{self._desc}>"

class CompiledMessage:
    def __init__(self, parts: list[MessagePart]):
        self._parts = parts

    def __repr__(self) -> str:
        parts_repr = ", ".join(repr(p) for p in self._parts)
        return f"CompiledMessage([{parts_repr}])"

    def render(self, tokens: list) -> str:
        return "".join(
            part if isinstance(part, str) else part(tokens)
            for part in self._parts
        )

def _last_hangul(s: str) -> str:
    for ch in reversed(s):
        if '가' <= ch <= '힣':
            return ch
    return ""

def _select_josa(a: str, b: str, last_char: str) -> str:
    """
    받침 여부에 따라 a(받침 있음) / b(받침 없음) 선택.
    으로/로 계열: ㄹ받침이면 b로.
    """
    if not ('가' <= last_char <= '힣'):
        return b
    code = (ord(last_char) - 0xAC00) % 28
    if code == 0:
        return b
    if code == 8 and a.startswith("으") and b == a[1:]:  # ㄹ받침 + 으로/로 계열
        return b
    return a

def _merge_strings(parts: list[MessagePart]) -> list[MessagePart]:
    merged: list[MessagePart] = []
    for part in parts:
        if merged and isinstance(merged[-1], str) and isinstance(part, str):
            merged[-1] += part
        else:
            merged.append(part)
    return merged

def compile_message(parsed_msg: list, combo: tuple[Condition, ...], source: str = "") -> CompiledMessage:
    form_vals = [c.form for c in combo if isinstance(c, (TagAndFormCondition, FormCondition))]

    result: list[MessagePart] = []
    for node in parsed_msg:
        match node:
            case TextNode():
                result.append(node.value)
            case TagNode(name="form", index=i):
                if i >= len(form_vals):
                    msg = (
                        f"{{form[{i}]}} is out of range: "
                        f"only {len(form_vals)} form condition(s) exist (indices 0–{len(form_vals)-1})"
                    )
                    if source:
                        msg += f"\n  in: {source}"
                    raise IndexError(msg)
                result.append(form_vals[i])
            case TagNode(name="dform", index=i):
                result.append(_DynamicPart(lambda tokens, i=i: tokens[i].form, f"dform[{i}]"))
            case TagNode(name="dtag", index=i):
                result.append(_DynamicPart(lambda tokens, i=i: tokens[i].tag, f"dtag[{i}]"))
            case QuotedNode():
                result.append(node.value)
            case MethodNode():
                result.append(_compile_method(node, form_vals, result, source))

    return CompiledMessage(_merge_strings(result))

def _compile_method(node: MethodNode, form_vals: list[str], result: list[MessagePart], source: str = "") -> MessagePart:
    if node.name == "batchim":
        return _compile_batchim(node, form_vals, result, source)

    method_spec = MESSAGE_METHODS[node.name]
    compiled_args = [
        tuple(_compile_tuple_item(item, form_vals) for item in arg.items)
        for arg in node.args
    ]

    method_spec.validate_func(node.args)

    if any(callable(part) for arg in compiled_args for part in arg):
        def dynamic(tokens, args=compiled_args, fn=method_spec.func):
            resolved = [
                tuple(p if isinstance(p, str) else p(tokens) for p in arg)
                for arg in args
            ]
            return fn(resolved)
        desc_args = ", ".join(
            "(" + ", ".join(repr(p) for p in arg) + ")"
            for arg in compiled_args
        )
        return _DynamicPart(dynamic, f"{node.name}({desc_args})")

    return method_spec.func(compiled_args)  # type: ignore[misc]

def _compile_batchim(node: MethodNode, form_vals: list[str], result: list[MessagePart], source: str = "") -> MessagePart:
    if not result:
        msg = "batchim() requires a preceding expression in the message"
        if source:
            msg += f"\n  in: {source}"
        raise ValueError(msg)

    MESSAGE_METHODS["batchim"].validate_func(node.args)

    a: str = node.args[0].items[0].value  # 받침 있음 (e.g. "으로")
    b: str = node.args[0].items[1].value  # 받침 없음 (e.g. "로")

    # 역방향으로 스캔: 한글 없는 정적 파트는 건너뜀, 동적 파트를 만나면 런타임으로 전환
    for part in reversed(result):
        if isinstance(part, str):
            ch = _last_hangul(part)
            if ch:
                return _select_josa(a, b, ch)
        else:  # _DynamicPart — 런타임에 스캔
            preceding = list(result)
            def dynamic(tokens, a=a, b=b, parts=preceding):
                for p in reversed(parts):
                    if isinstance(p, str):
                        ch = _last_hangul(p)
                        if ch:
                            return _select_josa(a, b, ch)
                    else:
                        ch = _last_hangul(p(tokens))
                        if ch:
                            return _select_josa(a, b, ch)
                return _select_josa(a, b, "")
            return _DynamicPart(dynamic, f"batchim({a!r},{b!r})")

    return _select_josa(a, b, "")

def _compile_tuple_item(item, form_vals: list[str]) -> MessagePart:
    match item:
        case QuotedNode():
            try:
                return Tag[item.value].value
            except KeyError:
                return item.value
        case TagNode(name="form", index=i):
            return form_vals[i]
        case TagNode(name="dform", index=i):
            return _DynamicPart(lambda tokens, i=i: tokens[i].form, f"dform[{i}]")
        case TagNode(name="dtag", index=i):
            return _DynamicPart(lambda tokens, i=i: tokens[i].tag, f"dtag[{i}]")
        case default:
            raise ValueError(default)
                    
@dataclass(frozen=True, slots=True)
class _TagSet:
    """AND 내부에서 여러 태그를 묶는 용도. Condition이 아님."""
    tags: set[Tag]

@dataclass(frozen=True, slots=True)
class _FormSet:
    """AND 내부에서 여러 폼을 묶는 용도. Condition이 아님."""
    forms: set[str]

class _RuleStepData:
    def __init__(self, conditions):
        self.conditions: list[Condition] = conditions
        self.spacing_rule: SpacingRule = SpacingRule.ANY
        self.is_optional: bool = False
        self.is_context: bool = False
        
    def __repr__(self):
        return f"_RuleStepData(conditions={self.conditions}, spacing_rule={self.spacing_rule}, is_optional={self.is_optional}, is_context={self.is_context})"

class RuleBuilder:
    def __init__(self, error_type: SpellErrorType):
        self.steps: list[_RuleStepData] = []
        self.message: str | None = None
        self.error_type: SpellErrorType = error_type
        self.rule_id: str = ""

    def tag(self, tag: str):
        self.steps.append(_RuleStepData([TagCondition(tag=tag)]))
        return self

    def tags(self, tag_set: set[Tag]):
        self.steps.append(_RuleStepData([TagCondition(tag=t) for t in tag_set]))
        return self
    
    def form(self, form: str):
        self.steps.append(_RuleStepData([FormCondition(form=form)]))
        return self

    def forms(self, form_set: set[str]):
        self.steps.append(_RuleStepData([FormCondition(form=f) for f in form_set]))
        return self
    
    def lemma(self, lemma: str):
        self.steps.append(_RuleStepData([LemmaCondition(lemma=lemma)]))
        return self

    def batchim(self, b: str):
        self.steps.append(_RuleStepData([BatchimCondition(batchim=b)]))
        return self
    
    def any_batchim(self):
        self.steps.append(_RuleStepData([AnyBatchimCondition()]))
        return self
    
    def no_batchim(self):
        self.steps.append(_RuleStepData([BatchimCondition(batchim="")]))
        return self
    
    def any(self):
        self.steps.append(_RuleStepData([AnyCondition()]))
        return self
    
    def tag_form(self, tag: str, form: str):
        self.steps.append(_RuleStepData([TagAndFormCondition(form=form, tag=tag)]))
        return self
    
    def first(self):
        self.steps.append(_RuleStepData([FirstTokenCondition()]))
        return self
    
    def length(self, n: int):
        self.steps.append(_RuleStepData([LengthCondition(length=n)]))
        return self
    
    def AND(self, *params: AndParam):
        optimized = _optimize_and(params)
        self.steps.append(_RuleStepData(optimized))
        return self

    def OR(self, *conditions: Condition):
        self.steps.append(_RuleStepData(list(conditions)))
        return self
    
    def NOT(self, condition: "Condition | _TagSet | _FormSet"):
        self.steps.append(_RuleStepData([NotCondition(_resolve_to_condition(condition))]))
        return self

    def _set_space(self, spacing_rule: SpacingRule):
        if not self.steps:
            raise ValueError("No condition to set a spacing rule. Call a condition method first.")
        if spacing_rule not in SpacingRule:
            raise ValueError(f"{spacing_rule} is not a member of SpacingRule class.")
        self.steps[-1].spacing_rule = spacing_rule

    def if_spaced(self):
        self._set_space(SpacingRule.SPACED)
        return self

    def if_not_spaced(self):
        self._set_space(SpacingRule.ATTACHED)
        return self
    
    def context(self):
        if not self.steps:
            raise ValueError("No condition to set context flag. Call a condition method first.")
        if self.steps[-1].is_context:
            warnings.warn("Context flag is already set on this condition.", stacklevel=2)
        
        self.steps[-1].is_context = True
        return self

    def opt(self):
        """조건을 선택적으로 만드는 메서드.

        첫 번째 조건을 Optional로 설정하면 ValueError.
        (첫 번째 조건 optional은 의미가 없음)
        """
        if not self.steps:
            raise ValueError("No condition to make optional. Call a condition method first.")
        if len(self.steps) == 1:
            raise ValueError("First condition can't be optional. Optional conditions must come after required ones.")
        self.steps[-1].is_optional = True
        return self

    def msg(self, input_msg: str):
        """에러 메시지를 입력하는 메서드.
        에러 메시지는 반드시 입력해야 함.
        
        {form}으로 form 조건을 지정할 수 있음.
        
        {form[0]}: 0번째 form 조건.(인덱스 필수)
        {dform[0]}: 0번째 매칭된 토큰의 form.(인덱스 필수)
        {dtag[0]}: 0번째 매칭된 토큰의 tag.(인덱스 필수)
        
        merge: 두 개 이상의 형태소를 합쳐 주는 메서드. merge((form, tag), (form, tag)...)로 사용.
        batchim: batchim 앞에 있는 유효한 한글에 받침을 붙여 주는 메서드. batchim("받침없을때", "받침있을때")로 사용.
        
        """
        self.message = input_msg
        return self
    
    def errtype(self, error_type: SpellErrorType):
        # init에서 설정하고 있지만 중간에 개별적으로 바꾸고 싶을 경우를 위해 메서드 준비
        self.error_type = error_type
        return self
    
    def id(self, rule_id: str):
        self.rule_id = rule_id
        return self

    def _validate_buildable(self):
        errors = []
        if not self.steps:
            errors.append("At least one condition must be added.")
        if self.message is None:
            errors.append("Error message must be set using msg().")
        if self.error_type == SpellErrorType.NOT_SET:
            errors.append("Error type has not been set. Use errtype() to set it.")
        elif self.error_type == SpellErrorType.NEED_ML_JUDGE and self.rule_id == "":
            errors.append("NEED_ML_JUDGE type requires a rule_id.")
        if self.steps and not any((not s.is_context) and (not s.is_optional) for s in self.steps):
            errors.append("At least one required (non-context, non-optional) condition must be added.")

        if errors:
            raise ValueError(
                "Spell build failed:\n- " + "\n- ".join(errors)
                + f"\nconditions: {self.steps}"
            )

    def build(self) -> list[KoSpellRules]:
        self._validate_buildable()

        results: list[KoSpellRules] = []
        parsed_msg = parser.parse(tokenizer.tokenize(self.message), source=self.message)
        
        for combo in product(*(step.conditions for step in self.steps)):
            rule_steps: RuleSteps = [
                (cond, step.spacing_rule, step.is_optional, step.is_context)
                for cond, step in zip(combo, self.steps)
            ]
            compiled_msg = compile_message(parsed_msg, combo, source=self.message)
            results.append((rule_steps, compiled_msg, self.error_type, self.rule_id))

        return results

def tag(t: str) -> TagCondition:
    return TagCondition(tag=t)

def tags(ts: set[Tag]) -> _TagSet:
    return _TagSet(tags=ts)

def form(f: str) -> FormCondition:
    return FormCondition(form=f)

def forms(fs: set[str]) -> _FormSet:
    return _FormSet(forms=fs)

def tag_form(t: str, f: str) -> TagAndFormCondition:
    return TagAndFormCondition(form=f, tag=t)

def lemma(l: str) -> LemmaCondition:
    return LemmaCondition(lemma=l)

def length(n: int) -> LengthCondition:
    return LengthCondition(length=n)

def batchim(b: str) -> BatchimCondition:
    return BatchimCondition(batchim=b)

def any_batchim() -> AnyBatchimCondition:
    return AnyBatchimCondition()

def no_batchim() -> BatchimCondition:
    return BatchimCondition(batchim="")

def first() -> FirstTokenCondition:
    return FirstTokenCondition()

def _resolve_to_condition(p: AndParam) -> Condition:
    """_TagSet/_FormSet → 런타임 Condition으로 변환. 이미 Condition이면 그대로."""
    if isinstance(p, _TagSet):
        if len(p.tags) == 1:
            return TagCondition(tag=next(iter(p.tags)))
        return TagSetCondition(tags=frozenset(p.tags))
    if isinstance(p, _FormSet):
        if len(p.forms) == 1:
            return FormCondition(form=next(iter(p.forms)))
        return FormSetCondition(forms=frozenset(p.forms))
    return p  # 이미 Condition

def NOT(condition: "Condition | _TagSet | _FormSet") -> NotCondition:
    return NotCondition(_resolve_to_condition(condition))

def _optimize_and(params: tuple[AndParam, ...]) -> list[Condition]:
    """Tags와 Forms를 AND로 묶을 경우, dictionary를 이용한 O(1) 조회가 쉽도록 각 조건을 분류하는 메서드.

    AND(Tag, Form) -> TagAndFormCondtion로 최적화(Tags/Form, Tag/Forms, Tags/Forms도 동일)
    
    기타 -> fallback으로 빠지는 AndCondition 생성
    
    """
    tag_values: list[str] = []
    form_values: list[str] = []
    other_conds: list[Condition] = []

    for p in params:
        if isinstance(p, _TagSet):
            tag_values.extend(p.tags)
        elif isinstance(p, _FormSet):
            form_values.extend(p.forms)
        elif isinstance(p, TagCondition):
            tag_values.append(p.tag)
        elif isinstance(p, FormCondition):
            form_values.append(p.form)
        elif isinstance(p, Condition):
            other_conds.append(p)
        else:
            raise TypeError(f"Unsupported AND parameter type: {type(p)}")

    if tag_values and form_values:
        tf_combos: list[Condition]= [
            TagAndFormCondition(form=f, tag=t)
            for t, f in product(tag_values, form_values)
        ]
        if other_conds:
            return [
                AndCondition(conditions=(tf, *other_conds))
                for tf in tf_combos
            ]
        return tf_combos

    resolved = [_resolve_to_condition(p) for p in params]
    return [AndCondition(conditions=tuple(resolved))]

def OR(*conditions: Condition) -> OrCondition:
    return OrCondition(conditions=tuple(conditions))

def AND(*params: AndParam) -> Condition:
    flat_params: list[AndParam] = []
    for p in params:
        if isinstance(p, AndCondition):
            flat_params.extend(p.conditions)
        else:
            flat_params.append(p)

    optimized = _optimize_and(tuple(flat_params))
    if len(optimized) == 1:
        return optimized[0]
    return OrCondition(conditions=tuple(optimized))