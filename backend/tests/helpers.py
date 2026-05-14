from src.engines.spell_checker import SpellChecker
from src.models.interface import SpellError
from src.tokenizations.ko_tokenizer import KoTokenizer
from src.models.interface import Tag, SpellErrorType

def tokenize_and_check(checker: SpellChecker, tokenizer: KoTokenizer, text: str) -> list[SpellError]:
    tokens = tokenizer.tokenize(text)
    return list(checker.check(tokens))

def assert_error(errors: list[SpellError], tokens: list | None = None):
    token_info = "\nToken: " + ", ".join(f"{t.form}/{Tag(t.tag).name}" for t in tokens) if tokens else ""
    assert errors != [], f"Expected errors, but no error asserted.{token_info}"

def assert_no_errors(errors: list[SpellError], checker, tokens: list | None = None,):
    token_info = "\nToken: " + ", ".join(f"{t.form}/{t.tag}" for t in tokens) if tokens else ""
    assert errors == [], f"Expected no errors, but got: {errors}\n{token_info}\n"
    
def assert_error_raw_text(errors: list[SpellError], text: str):
    assert errors != [], f"Expected errors, but no error aseerted. {text}"
    
def assert_no_errors_raw_text(errors: list, text: str):
    assert errors == [], f"Expected no errors, but got: {errors}{text}\n"
    
def check_error_type(errors: list[SpellError], error_type: SpellErrorType):
    for e in errors:
        if e.error_type == error_type:
            return
    error_types = list({e.error_type.name for e in errors})
    assert f"Expected {error_type} Error, but got: {", ".join(error_types)}"