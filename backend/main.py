import sys

from _core import RawStringSearcher
from src.tokenizations.ko_tokenizer import KoTokenizer
from src.engines.spell_checker import SpellChecker
from src.configs.spell_checker_config import SPELL_CHECK_RULES
from src.configs.raw_string_searcher_config import RAW_STRING_RULES
from src.models.interface import SpellError

print("초기화 실행 중")
tokenizer = KoTokenizer()
_ = tokenizer.tokenize("")
spell_check = SpellChecker(True)
raw_string_check = RawStringSearcher()

spell_check.add_rule_from_list(SPELL_CHECK_RULES)

for words, err_type in RAW_STRING_RULES:
    for word_group, msg in words:
        for word in word_group:
            raw_string_check.add_word(word, msg, "RAW")
            
print("초기화 완료")

if __name__ == "__main__":
    try:
        while True:
            u_input = input(" 》 검사할 텍스트를 입력하세요.\n")
            res = [SpellError(error_type=r[0], error_message=r[1], start_index=r[2], end_index=r[3]) for r in raw_string_check.search(u_input)]
            res.extend(spell_check.check(tokenizer.tokenize(u_input)))

            if res:
                print("\n------------------ 결과")
                for i, r in enumerate(res):
                    print(f"오류 {i+1}")
                    print(f"error type: {r.error_type}")
                    print(f"error message: {r.error_message}")
                    if r.debug_path:
                        print(f"debug path: {r.debug_path}")
                    print("")
            else:
                print("\n결과가 없습니다.\n")
            
    except:
        sys.exit()