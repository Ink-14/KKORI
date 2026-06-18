from enum import StrEnum, Enum, auto
from typing import  Protocol, TypeAlias
from dataclasses import dataclass

RuleId: TypeAlias = str
DebugPath: TypeAlias = str
DetailedMessage: TypeAlias = str

class SpellErrorType(Enum):
    NOT_SET = auto()

    SPELLING_RAW = auto()
    SPACING_RAW = auto()
    MEANING_RAW = auto()
    LOANWORD_RAW = auto()

    SPACING = auto()
    MEANING = auto()
    SPELLING = auto()
    SPECIFIC = auto()
    LOANWORD = auto()
    COMPLEX = auto()

    WARNING = auto()
    NEED_ML_JUDGE = auto()
    
    TEST = auto()

@dataclass(frozen=True, slots=True)
class SpellError:
    
    """
    검사 결과를 담는 데이터 구조입니다.
    
        error_type (SpellErrorType): 발생한 오류의 종류.
        error_message (str): 발생한 에러에 대한 상세 메시지.
        start_index (int): 에러가 발생한 부분의 시작 인덱스.
        end_index (int): 에러가 발생한 부분의 끝 인덱스.
        rule_id (str): 규칙의 id.
        detailed (str): 규칙에 대한 세부 설명.
        debug_path (str | None): NFA 엔진 경로 추적용 속성.

    """
    error_type: SpellErrorType
    error_message: str
    start_index: int
    end_index: int
    rule_id: str
    detailed: DetailedMessage
    debug_path: str | None = None

class Tag(StrEnum):
    일반명사 = 'NNG'
    고유명사 = 'NNP'
    의존명사 = 'NNB'
    수사 = 'NR'
    대명사 = 'NP'
    동사 = 'VV'
    동사불규칙활용 = 'VV-R'
    동사규칙활용 = 'VV-I'
    형용사 = 'VA'
    형용사불규칙활용 = 'VA-R'
    형용사규칙활용 = 'VA-I'
    보조용언 = 'VX'
    보조용언불규칙활용 = 'VX-R'
    보조용언규칙활용 = 'VX-I'
    긍정지정사 = 'VCP'
    부정지정사 = 'VCN'
    관형사 = 'MM'
    일반부사 = 'MAG'
    접속부사 = 'MAJ'
    감탄사 = 'IC'
    주격조사 = 'JKS'
    보격조사 = 'JKC'
    관형격조사 = 'JKG'
    목적격조사 = 'JKO'
    부사격조사 = 'JKB'
    호격조사 = 'JKV'
    인용격조사 = 'JKQ'
    보조사 = 'JX'
    접속조사 = 'JC'
    선어말어미 = 'EP'
    종결어미 = 'EF'
    연결어미 = 'EC'
    명사형전성어미 = 'ETN'
    관형사형전성어미 = 'ETM'
    체언접두사 = 'XPN'
    명사파생접미사 = 'XSN'
    동사파생접미사 = 'XSV'
    형용사파생접미사 = 'XSA'
    형용사파생접미사불규칙활용 = 'XSA-R'
    형용사파생접미사규칙활용 = 'XSA-I'
    부사파생접미사 = 'XSM'
    어근 = 'XR'
    종결부호 = 'SF'
    구분부호 = 'SP'
    인용부호괄호 = 'SS'
    여는부호 = 'SSO'
    닫는부호 = 'SSC'
    줄임표 = 'SE'
    붙임표 = 'SO'
    기타특수문자 = 'SW'
    알파벳 = 'SL'
    한자 = 'SH'
    숫자 = 'SN'
    글머리 = 'SB'
    분석불능 = 'UN'
    URL주소 = 'W_URL'
    이메일주소 = 'W_EMAIL'
    해시태그 = 'W_HASHTAG'
    멘션 = 'W_MENTION'
    일련번호 = 'W_SERIAL'
    이모지 = 'W_EMOJI'
    덧붙은받침 = 'Z_CODA'
    사이시옷 = 'Z_SIOT'
    사용자정의태그0 = 'USER0'
    사용자정의태그1 = 'USER1'
    사용자정의태그2 = 'USER2'
    사용자정의태그3 = 'USER3'
    사용자정의태그4 = 'USER4'
    
class TagGroup:
    체언 = {Tag.일반명사,
            Tag.고유명사,
            Tag.의존명사,
            Tag.수사,
            Tag.대명사
        }
    용언 = {Tag.동사,
            Tag.동사불규칙활용,
            Tag.동사규칙활용,
            Tag.형용사,
            Tag.형용사불규칙활용,
            Tag.형용사규칙활용,
            Tag.보조용언,
            Tag.보조용언불규칙활용,
            Tag.보조용언규칙활용,
            Tag.긍정지정사,
            Tag.부정지정사
        }
    부사 = {Tag.일반부사,
            Tag.접속부사
        }
    조사 = {Tag.주격조사,
            Tag.보격조사,
            Tag.관형격조사,
            Tag.목적격조사,
            Tag.부사격조사,
            Tag.호격조사,
            Tag.인용격조사,
            Tag.보조사,
            Tag.접속조사
        }
    어미 = {Tag.선어말어미,
            Tag.종결어미,
            Tag.연결어미,
            Tag.명사형전성어미,
            Tag.관형사형전성어미
        }
    접두사 = {Tag.체언접두사}
    접미사 = {Tag.명사파생접미사,
            Tag.동사파생접미사,
            Tag.형용사파생접미사,
            Tag.형용사파생접미사불규칙활용,
            Tag.형용사파생접미사규칙활용,
            Tag.부사파생접미사
        }
    특수문자 = {Tag.종결부호,
                Tag.구분부호,
                Tag.인용부호괄호,
                Tag.여는부호,
                Tag.닫는부호,
                Tag.줄임표,
                Tag.붙임표,
                Tag.기타특수문자,
                Tag.알파벳,
                Tag.한자,
                Tag.숫자,
                Tag.글머리
            }
    웹 = {Tag.URL주소,
        Tag.이메일주소,
        Tag.해시태그,
        Tag.멘션,
        Tag.일련번호,
        Tag.이모지
        }
    전부 = set(Tag)

TAG_NAMES = {i.name for i in Tag}
TAG2IDX = {"__UNK__": 0}
TAGNAME2IDX = {"__UNK__": 0}

for idx, tag in enumerate(Tag):
    TAG2IDX[tag.value] = idx + 1
    TAGNAME2IDX[tag.name] = idx + 1

class KoToken(Protocol):
    """한국어 토큰 인터페이스.

    Attributes:
        form (str): 형태소의 문자열 표기.
        tag (str | Tag): 세종 품사 태그.
        start (int): 형태소가 등장하는 위치.
        end (int): 형태소가 끝나는 위치.
        len (int): 형태소의 길이.
        lemma (str): 형태소의 사전 표제형.
        oov (bool): Out-Of-Vocabulary 단어 여부.
    """
    form: str
    tag: str
    start: int
    end: int
    len: int
    lemma: str
    oov: bool

class InternalToken(KoToken, Protocol):
    """받침 정보가 추가된 토큰 인터페이스."""
    batchim: int