from typing import NamedTuple

from src.models.interface import Tag, KoToken
from src.utils.hangul import get_normal_batchim

class Word(NamedTuple):
    form: str
    tag: str
    score: float

class PreAnalyzedMorph(NamedTuple):
    word: str
    elements: list[tuple[str, str]]
    score: float

def make_없다_VA_MAG_words(words: list[tuple[str, float]], default_score: float = 0.0) -> list[Word]:
    result = []
    for word, score in words:
        if score == 0.0 and default_score != 0.0:
            score = default_score

        VA_form = word + "없"
        MAG_form = word + "없이"
        result.append((VA_form, "VA", score))
        result.append((MAG_form, "MAG", score))

    return result

def make_들다_complex_verbs(words: list[tuple[str, float]], default_score: float = 10.0) -> list[tuple[Word, list[PreAnalyzedMorph]]]:
    errors = []
    result = []

    for word, score in words:
        morph_result = []

        if len(word) == 0:
            errors.append("들다_complex_verbs file has a empty row.")
            continue

        if get_normal_batchim(word[-1]) != "ㄹ":
            errors.append(f"들다_complex verbs file has invalid word. {word}")
            continue

        # word
        if score == 10.0 and default_score != 0.0:
            score = default_score

        # pre_analyzed sentence
        other_characters = word[:-1]
        original_last_charpoint = ord(word[-1])

        no_batchim_form = chr(original_last_charpoint - 8)
        ㄴ_batchim_form = chr(original_last_charpoint - 4)

        base_lists = [(word, "VV")]

        든_lists = base_lists.copy()
        든_lists.append(("ᆫ", "ETM"))
        드는_lists = base_lists.copy()
        드는_lists.append(("는", "ETM"))
        든다_lists = base_lists.copy()
        든다_lists.append(("ᆫ다", "EF"))

        morph_result.append(PreAnalyzedMorph(other_characters + ㄴ_batchim_form, 든_lists, score))
        morph_result.append(PreAnalyzedMorph(other_characters + no_batchim_form + "는", 드는_lists, score))
        morph_result.append(PreAnalyzedMorph(other_characters + ㄴ_batchim_form + "다", 든다_lists, score))

        result.append((Word(form=word, tag="VV", score=score), morph_result))

    if errors:
        raise ValueError(f"들다_complex_verbs file had invalid rows: {errors}")

    return result

def pprint_tokens(tokens: list[KoToken], detailed: bool = False):
    for i, token in enumerate(tokens):
        if detailed:
            spaced = False
            if i > 0:
                if token.start - tokens[i-1].end > 0:
                    spaced = True

            print(f"{i} form: {token.form} tag: {Tag(token.tag).name}, raw_form: {token.raw_form}, lemma: {token.lemma}, word_position: {token.word_position}, spaced: {spaced}")
        else:
            print(f"{i} {token.form}({token.base_form}) -- {Tag(token.tag).name}")

def _print_with_indent(text: str, indent: int):
    idt = " "
    print(idt * indent + text)