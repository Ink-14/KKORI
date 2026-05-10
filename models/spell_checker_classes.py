from enum import Enum, auto
from abc import ABC, abstractmethod
from dataclasses import dataclass

from korean_spell_checker.models.interface import InternalToken

class SpacingRule(Enum):
    """해당 단어 앞에 띄어쓰기 있는지 여부.

    Args:
        SPACED: 띄어져 있는 상태.
        ATTACHED: 붙어 있는 상태.
        ANY: 아무 상태나 허용.
    """
    ANY = 0
    SPACED = 1
    ATTACHED = 2

@dataclass(frozen=True, slots=True)
class Condition(ABC):
    @abstractmethod
    def match(self, token: InternalToken) -> bool:
        """상속받은 클래스에서 구현해야 하는 추상 메서드. 조건 만족 시 True를 반환하도록 구현해야 함."""
        raise NotImplementedError

@dataclass(frozen=True, slots=True)
class TagCondition(Condition):
    tag: str
        
    def match(self, token: InternalToken) -> bool:
        return token.tag == self.tag

@dataclass(frozen=True, slots=True)
class FormCondition(Condition):
    form: str

    def match(self, token: InternalToken) -> bool:
        return token.form == self.form
    
@dataclass(frozen=True, slots=True)
class TagAndFormCondition(Condition):
    """Tag와 Form을 동시에 검사하는 메서드. (form, tag)의 튜플을 이용해 O(1) 검사할 것이므로 TagCondition과 FormCondition을 and로 조합하지 않고 별도 메서드로 분리.
    """
    form: str
    tag: str
    
    def match(self, token: InternalToken) -> bool:
        return token.form == self.form and token.tag == self.tag

@dataclass(frozen=True, slots=True)
class LemmaCondition(Condition):
    lemma: str

    def match(self, token: InternalToken) -> bool:
        return token.lemma == self.lemma

@dataclass(frozen=True, slots=True)
class AnyCondition(Condition):
    def match(self, token: InternalToken) -> bool:
        return True

@dataclass(frozen=True, slots=True)
class AnyBatchimCondition(Condition):
    def match(self, token: InternalToken) -> bool:
        return token.batchim != ""

@dataclass(frozen=True, slots=True)
class BatchimCondition(Condition):
    batchim: str

    def match(self, token: InternalToken) -> bool:
        return token.batchim == self.batchim

@dataclass(frozen=True, slots=True)
class LengthCondition(Condition):
    length: int

    def match(self, token: InternalToken) -> bool:
        return token.len >= self.length
    
@dataclass(frozen=True, slots=True)
class FirstTokenCondition(Condition):
    def match(self, token: InternalToken) -> bool:
        return token.start == 0

@dataclass(frozen=True, slots=True)
class TagSetCondition(Condition):
    tags: frozenset[str]
    
    def match(self, token: InternalToken) -> bool:
        return token.tag in self.tags

@dataclass(frozen=True, slots=True)
class FormSetCondition(Condition):
    forms: frozenset[str]
    
    def match(self, token: InternalToken) -> bool:
        return token.form in self.forms
            
@dataclass(frozen=True, slots=True)
class AndCondition(Condition):
    conditions: tuple[Condition, ...]

    def match(self, token: InternalToken) -> bool:
        for cond in self.conditions:
            if not cond.match(token):
                return False
        return True

@dataclass(frozen=True, slots=True)
class OrCondition(Condition):
    conditions: tuple[Condition, ...]

    def match(self, token):
        for cond in self.conditions:
            if cond.match(token):
                return True
        return False
    
@dataclass(frozen=True, slots=True)
class NotCondition(Condition):
    condition: Condition

    def match(self, token: InternalToken) -> bool:
        return not self.condition.match(token)