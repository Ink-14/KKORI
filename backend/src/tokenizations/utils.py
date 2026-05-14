from src.models.interface import Tag, KoToken

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