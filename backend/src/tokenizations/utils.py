from src.models.interface import Tag, KoToken

def make_없다_VA_MAG_words(words : list[tuple[str, float]], default_score: float = 0.0) -> list[tuple[str, str, float]]:
    result_words = []
    for word, score in words:
        if score == 0.0 and default_score != 0.0:
            score = default_score

        VA_form = word + "없"
        MAG_form = word + "없이"
        result_words.append((VA_form, "VA", score))
        result_words.append((MAG_form, "MAG", score))
    return result_words

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