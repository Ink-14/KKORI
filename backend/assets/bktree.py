"""BK-Tree: 한글 자모 분리 Damerau-Levenshtein 기반 근사 검색.

pickle 포함 시 이 파일이 임포트 가능한 경로에 있어야 합니다.
quick_launcher.pyw 가 scripts/ 를 sys.path 에 추가하므로
같은 scripts/ 폴더에 위치하면 됩니다.
"""
from jamo import h2j
from rapidfuzz.distance import DamerauLevenshtein as _DL

def _dist(a: str, b: str) -> int:
    """jamo 분리 후 Damerau-Levenshtein 거리."""
    return _DL.distance(h2j(a), h2j(b))


class BKTree:
    """BK-Tree 노드 (iterative insert, pickle 가능)."""
    __slots__ = ('word', 'children')

    def __init__(self, word: str):
        self.word: str = word
        self.children: dict[int, 'BKTree'] = {}

    def insert(self, word: str) -> None:
        node = self
        while True:
            d = _dist(node.word, word)
            if d == 0:
                return  # 중복
            if d in node.children:
                node = node.children[d]
            else:
                node.children[d] = BKTree(word)
                return

    def search(self, query: str, threshold: int) -> list[tuple[int, str]]:
        """(distance, word) 리스트를 거리 오름차순으로 반환."""
        out: list[tuple[int, str]] = []
        stack = [self]
        while stack:
            node = stack.pop()
            d = _dist(node.word, query)
            if d <= threshold:
                out.append((d, node.word))
            lo, hi = d - threshold, d + threshold
            for cd, child in node.children.items():
                if lo <= cd <= hi:
                    stack.append(child)
        out.sort()
        return out


def build(words: list[str]) -> 'BKTree | None':
    """단어 리스트에서 BK-Tree를 생성. 빈 리스트면 None 반환."""
    it = iter(words)
    try:
        root = BKTree(next(it))
    except StopIteration:
        return None
    for w in it:
        root.insert(w)
    return root
