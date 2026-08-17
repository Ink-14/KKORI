from bisect import bisect_right

from _core import RustRawStringSearcher
from src.models.interface import SpellError, SpellErrorType, SPELL_ERROR_TYPE_PRIORITY

class _InnerRawSearcher(RustRawStringSearcher):
    def add_word_from_list(self, rule_list: list[tuple[list[tuple[tuple[str, ...], str]], SpellErrorType, str]]):
        for words, err_type, rule_id in rule_list:
            for word_group, msg in words:
                for word in word_group:
                    super().add_word(word=word, msg=msg, error_type=err_type.name, rule_id=rule_id)

    def search(self, word: str) -> list[SpellError]:
        return [SpellError(error_type=SpellErrorType[r[0]], error_message=r[1], start_index=r[2], end_index=r[3], rule_id=r[4], detailed="", priority=SPELL_ERROR_TYPE_PRIORITY[SpellErrorType[r[0]]])
            for r in super().search_raw(word)]

    def search_batch(self, words: list[str]) -> list[list[SpellError]]:
        """문자열 배치를 받아 병렬 검색."""
        return [
            [SpellError(error_type=SpellErrorType[r[0]], error_message=r[1], start_index=r[2], end_index=r[3], rule_id=r[4], detailed="", priority=SPELL_ERROR_TYPE_PRIORITY[SpellErrorType[r[0]]]) for r in raw]
            for raw in super().search_raw_batch(words)
        ]

class RawStringSearcher:
    def __init__(self):
        self.black_searcher: _InnerRawSearcher = _InnerRawSearcher()
        self.white_searcher: _InnerRawSearcher = _InnerRawSearcher()
        self._has_white: bool = False

    def add_word_from_list(self, rule_list: list[tuple[list[tuple[tuple[str, ...], str]], SpellErrorType, str]]) -> None:
        self.black_searcher.add_word_from_list(rule_list)

    def add_whitelist_word(self, word: str) -> None:
        self.white_searcher.add_word_from_list(
            [([((word,), "")], SpellErrorType.WHITELIST, "")]
        )
        self._has_white = True

    def _filter(self, black_result: list[SpellError], white_result: list[SpellError]) -> list[SpellError]:
        white_result.sort(key=lambda x: x[2])

        running_max = float('-inf')
        prefix_max = []
        for r in white_result:
            running_max = max(running_max, r[3])
            prefix_max.append(running_max)

        w_starts = [r[2] for r in white_result]

        result = []
        for error_type, msg, bs, be, rule_id in black_result:
            k = bisect_right(w_starts, bs)
            if k > 0 and prefix_max[k-1] >= be:
                continue
            parsed_type = SpellErrorType[error_type]
            result.append(SpellError(
                error_type=parsed_type,
                error_message=msg,
                start_index=bs,
                end_index=be,
                rule_id=rule_id,
                detailed="",
                priority=SPELL_ERROR_TYPE_PRIORITY[parsed_type],
            ))
        return result

    def _to_spell_errors(self, black_result: list[SpellError]) -> list[SpellError]:
        return [
            SpellError(
                error_type=SpellErrorType[r[0]],
                error_message=r[1],
                start_index=r[2],
                end_index=r[3],
                rule_id=r[4],
                detailed="",
                priority=SPELL_ERROR_TYPE_PRIORITY[SpellErrorType[r[0]]],
            )
            for r in black_result
        ]

    def search(self, sentence: str) -> list[SpellError]:
        black_result = self.black_searcher.search_raw(sentence)
        if not self._has_white:
            return self._to_spell_errors(black_result)
        white_result = self.white_searcher.search_raw(sentence)
        return self._filter(black_result, white_result)

    def search_batch(self, sentences: list[str]) -> list[list[SpellError]]:
        black_results = self.black_searcher.search_raw_batch(sentences)
        if not self._has_white:
            return [self._to_spell_errors(br) for br in black_results]
        white_results = self.white_searcher.search_raw_batch(sentences)
        return [
            self._filter(black_result, white_result)
            for black_result, white_result in zip(black_results, white_results)
        ]