HANGUL_COMP_START = ord("가")
HANGUL_COMP_END = ord("힣")
HANGUL_JAMO_START = ord("ㄱ")
HANGUL_JAMO_END = ord("ㅣ")

JONGSEONG_IDX_POINT = 28
JUNGSEONG_IDX_POINT = 21
CHOSEONG_IDX_POINT = JUNGSEONG_IDX_POINT * JONGSEONG_IDX_POINT

CHO_LIST = ['ㄱ', 'ㄲ', 'ㄴ', 'ㄷ', 'ㄸ', 'ㄹ', 'ㅁ', 'ㅂ', 'ㅃ', 'ㅅ', 'ㅆ', 'ㅇ', 'ㅈ', 'ㅉ', 'ㅊ', 'ㅋ', 'ㅌ', 'ㅍ', 'ㅎ']
JUNG_LIST = ['ㅏ', 'ㅐ', 'ㅑ', 'ㅒ', 'ㅓ', 'ㅔ', 'ㅕ', 'ㅖ', 'ㅗ', 'ㅘ', 'ㅙ', 'ㅚ', 'ㅛ', 'ㅜ', 'ㅝ', 'ㅞ', 'ㅟ', 'ㅠ', 'ㅡ', 'ㅢ', 'ㅣ']
JONG_LIST = ['', 'ㄱ', 'ㄲ', 'ㄳ', 'ㄴ', 'ㄵ', 'ㄶ', 'ㄷ', 'ㄹ', 'ㄺ', 'ㄻ', 'ㄼ', 'ㄽ', 'ㄾ', 'ㄿ', 'ㅀ', 'ㅁ', 'ㅂ', 'ㅄ', 'ㅅ', 'ㅆ', 'ㅇ', 'ㅈ', 'ㅊ', 'ㅋ', 'ㅌ', 'ㅍ', 'ㅎ']
BATCHIM_LIST = ['', 'ᆨ', 'ᆩ', 'ᆪ', 'ᆫ', 'ᆬ', 'ᆭ', 'ᆮ', 'ᆯ', 'ᆰ', 'ᆱ', 'ᆲ', 'ᆳ', 'ᆴ', 'ᆵ', 'ᆶ', 'ᆷ', 'ᆸ', 'ᆹ', 'ᆺ', 'ᆻ', 'ᆼ', 'ᆽ', 'ᆾ', 'ᆿ', 'ᇀ', 'ᇁ', 'ᇂ']
BATCHIM_DICT = {"__UNK__": 0}
for i in BATCHIM_LIST:
    BATCHIM_DICT[i] = len(BATCHIM_DICT)

CHO_SET = {i for i in CHO_LIST}
JUNG_SET = {i for i in JUNG_LIST}
JONG_SET = {i for i in JONG_LIST}
JAMO_SET = CHO_SET | JUNG_SET | JONG_SET - {''}
JAEUM_SET = CHO_SET | JONG_SET
JAMO_CHARCODE_SET = {ord(i) for i in JAMO_SET}

def is_hangul(char: str):
    charpoint = ord(char)
    if HANGUL_COMP_START <= charpoint <= HANGUL_COMP_END or HANGUL_JAMO_START <= charpoint <= HANGUL_JAMO_END:
        return True
    return False

def is_hangul_syllable(char: str):
    if HANGUL_COMP_START <= ord(char) <= HANGUL_COMP_END:
        return True
    return False

def convert_to_hangul_charpoint(char: str) -> int:
    return ord(char) - HANGUL_COMP_START

def is_jamo(char: str) -> bool:
    return char in JAMO_SET

def get_choseong(char: str) -> str:
    return CHO_LIST[(convert_to_hangul_charpoint(char) // CHOSEONG_IDX_POINT)]

def get_jungseong(char: str) -> str:
    return JUNG_LIST[(convert_to_hangul_charpoint(char) % CHOSEONG_IDX_POINT) // JONGSEONG_IDX_POINT]

def get_jongseong(char: str) -> str:
    return JONG_LIST[(convert_to_hangul_charpoint(char) % JONGSEONG_IDX_POINT)]

def get_compatible_batchim(char) -> str:
    return BATCHIM_LIST[(convert_to_hangul_charpoint(char) % JONGSEONG_IDX_POINT)]

def get_compatible_batchim_int(char: str) -> int:
    charpoint = ord(char)
    if HANGUL_COMP_START <= charpoint <= HANGUL_COMP_END:
        return (charpoint - HANGUL_COMP_START) % JONGSEONG_IDX_POINT + 1 # 0번은 '한글 아님'으로 예약
    else:
        return 0

def remove_batchim(char: str) -> str:
    if len(char) != 1:
        raise ValueError(f"single character expected, got '{char}'")

    code = ord(char)
    if not (HANGUL_COMP_START <= code <= HANGUL_COMP_END):
        return char

    jongseong_idx = (code - HANGUL_COMP_START) % JONGSEONG_IDX_POINT
    if jongseong_idx == 0:
        return char

    return chr(code - jongseong_idx)

def replace_batchim(char: str, jamo: str) -> str:
    if len(char) != 1:
        raise ValueError(f"single character expected, got '{char}'")

    code = ord(char)
    if not (HANGUL_COMP_START <= code <= HANGUL_COMP_END):
        return char

    base_code = ord(remove_batchim(char))
    jong_idx = JONG_LIST.index(jamo)
    return chr(base_code + jong_idx)