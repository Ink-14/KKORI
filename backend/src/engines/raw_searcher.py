from _core import RustRawStringSearcher
from src.models.interface import SpellError, SpellErrorType

class RawStringSearcher(RustRawStringSearcher):
    def add_word_from_list(self, rule_list: list[tuple[list[tuple[tuple[str, ...], str]], SpellErrorType, str]]):
        for words, err_type, rule_id in rule_list:
            for word_group, msg in words:
                for word in word_group:
                    super().add_word(word=word, msg=msg, error_type=err_type.name, rule_id=rule_id)
        
    def search(self, word: str) -> list[SpellError]:
        return [SpellError(error_type=SpellErrorType[r[0]], error_message=r[1], start_index=r[2], end_index=r[3], rule_id=r[4])
            for r in super().search_raw(word)]

    def search_batch(self, words: list[str]) -> list[list[SpellError]]:
        """문자열 배치를 받아 병렬 검색."""
        return [
            [SpellError(error_type=SpellErrorType[r[0]], error_message=r[1], start_index=r[2], end_index=r[3], rule_id=r[4]) for r in raw]
            for raw in super().search_raw_batch(words)
        ]