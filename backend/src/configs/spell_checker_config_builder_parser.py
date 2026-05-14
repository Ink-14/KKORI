from enum import StrEnum, auto
from dataclasses import dataclass
from typing import Callable

from src.tokenizations.ko_tokenizer import KoTokenizer
from src.models.interface import TAG_NAMES

@dataclass
class MethodSpec:
    min_args: int
    func: Callable | None
    validate_func: Callable
    uses_flat_args: bool = False

class TokenType(StrEnum):
    # strings
    RSTRING = auto()
    NUMBER = auto()
    ASCII = auto()
    QUOTED = auto()
    
    LPAREN = auto()
    RPAREN = auto()
    LBRACE = auto()
    RBRACE = auto()
    LBRACKET = auto()
    RBRACKET = auto()

    COMMA = auto()

    # methods
    METHOD = auto()

    # tags
    TAG = auto()

@dataclass
class TextNode:
    """{} 바깥의 일반 텍스트"""
    value: str

@dataclass
class TagNode:
    """form[0] 같은 것"""
    name: str
    index: int

@dataclass
class MethodNode:
    name: str
    args: list["TupleNode"]

@dataclass
class TupleNode:
    items: list

@dataclass
class QuotedNode:
    value: str

def _node_str(node) -> str:
    if isinstance(node, QuotedNode):
        return node.value
    if isinstance(node, TagNode):
        return node.name
    return str(node)

def validate_merge(*args):
    for arg in args:
        for node in arg:
            if len(node.items) > 2:
                raise ValueError(f"merge method expected tuple of 2 strings, but got {tuple(_node_str(i) for i in node.items)}")
            form_node, tag_node = node.items
            if isinstance(form_node, QuotedNode) and form_node.value == "":
                raise ValueError(f"merge method: form cannot be empty")
            if not isinstance(form_node, (QuotedNode, TagNode)):
                raise ValueError(f"merge method: first item must be a quoted string or tag")
            if isinstance(tag_node, TagNode):
                pass  # dtag/dform은 동적 처리, 검증 생략
            elif isinstance(tag_node, QuotedNode):
                if tag_node.value not in TAG_NAMES:
                    raise ValueError(f"merge method expected tag, but got {tag_node.value}")
            else:
                raise ValueError(f"merge method: second item must be a tag or quoted string")

def validate_batchim(args: list["TupleNode"]):
    if len(args) != 1:
        raise ValueError(f"batchim expects 1 argument tuple, got {len(args)}")
    items = args[0].items
    if len(items) != 2:
        raise ValueError(f"batchim expects 2 quoted strings (받침 있음, 받침 없음), got {len(items)}")
    for item in items:
        if not isinstance(item, QuotedNode):
            raise ValueError(f"batchim arguments must be quoted strings, got {type(item).__name__}")

MESSAGE_METHODS: dict[str, MethodSpec] = {
    "merge": MethodSpec(min_args=2, func=KoTokenizer().join, validate_func=validate_merge),
    "batchim": MethodSpec(min_args=1, func=None, validate_func=validate_batchim, uses_flat_args=True),
}

MESSAGE_STATIC_TAGS: set[str] = {"form"}
MESSAGE_DYNAMIC_TAGS: set[str] = {"dform", "dtag"}
MESSAGE_TAGS = MESSAGE_STATIC_TAGS | MESSAGE_DYNAMIC_TAGS

MESSAGE_PARENS: dict[str, TokenType] = {
    "(": TokenType.LPAREN,
    ")": TokenType.RPAREN,
    "{": TokenType.LBRACE,
    "}": TokenType.RBRACE,
    "[": TokenType.LBRACKET,
    "]": TokenType.RBRACKET,
}

class MessageToken():
    def __init__(self, type: TokenType, string: str, pos: int):
        self.type: TokenType = type
        self.string: str = string
        self.pos: int = pos
    
    def __repr__(self):
        return f"MessageToken({self.type.name}: '{self.string}')"
    
class MessageTokenizer:
    def __init__(self):
        self.parens = MESSAGE_PARENS
        self.tags = MESSAGE_TAGS
        self.methods = MESSAGE_METHODS.keys()
        self.special_characters = {
            ",": TokenType.COMMA
        }
    
    def tokenize(self, string: str) -> list[MessageToken]:
        if string == "":
            return []
        
        i = 0
        tokens = []
        
        def peek() -> str | None:
            return None if i >= len(string) else string[i]
        
        def advance() -> str:
            nonlocal i
            ch = string[i]
            i += 1
            return ch

        def consume_while(predicate) -> str:
            start = i
            while peek() is not None and predicate(peek()):
                advance()
            return string[start:i]
        
        def emit(type: TokenType, string: str, pos: int):
            tokens.append(MessageToken(type, string, pos))

        def _is_special(c: str) -> bool:
           return (
                (c.isalpha() and c.isascii())
                or c == "_"
                or c.isdigit()
                or c in self.parens
                or c in self.special_characters
                or c == '"'
            )

        while peek() is not None:
            ch = peek()
            start = i

            if (ch.isalpha() and ch.isascii()) or ch == "_":
                alphas = consume_while(lambda c: c.isascii() and (c.isalpha() or c == "_"))
                if alphas in self.methods:
                    emit(TokenType.METHOD, alphas, start)
                elif alphas in self.tags:
                    emit(TokenType.TAG, alphas, start)
                else:
                    emit(TokenType.ASCII, alphas, start)

            elif ch.isdigit():
                numbers = consume_while(str.isdigit)
                emit(TokenType.NUMBER, numbers, start)

            elif ch in self.parens:
                emit(self.parens[ch], ch, start)
                advance()

            elif ch == '"':
                advance()
                start = i
                while peek() is not None and peek() != '"':
                    advance()
                content = string[start:i]
                if peek() is None:
                    raise ValueError("unclosed quote")
                advance()
                emit(TokenType.QUOTED, content, start)

            elif ch in self.special_characters:
                emit(self.special_characters[ch], ch, start)
                advance()

            else:
                s = consume_while(lambda c: not _is_special(c))
                emit(TokenType.RSTRING, s, start)

        return tokens

def _format_parse_error(source: str, pos: int, length: int, msg: str) -> str:
    pointer = " " * pos + "^" * max(length, 1)
    return f"{msg}\n{source}\n{pointer}"

class MessageParser:
    def __init__(self):
        self.methods = MESSAGE_METHODS

    def parse(self, tokens: list[MessageToken], source: str = "") -> list[TextNode | TagNode | QuotedNode | MethodNode | TupleNode]:
        i = 0
        nodes = []

        def peek() -> MessageToken | None:
            return tokens[i] if i < len(tokens) else None

        def advance() -> MessageToken:
            nonlocal i
            token = tokens[i]
            i += 1
            return token

        def skip_whitespace():
            while peek() is not None and peek().type == TokenType.RSTRING and peek().string.isspace():
                advance()

        def expect(type: TokenType) -> MessageToken:
            token = peek()
            if token is None:
                msg = f"expected {type}, got end of input"
                raise ValueError(_format_parse_error(source, len(source), 1, msg) if source else msg)
            if token.type != type:
                msg = f"expected {type}, got {token}"
                raise ValueError(_format_parse_error(source, token.pos, len(token.string), msg) if source else msg)
            return advance()
        
        def parse_tag_expr() -> TagNode:
            expect(TokenType.LBRACE)
            name_token = expect(TokenType.TAG)
            expect(TokenType.LBRACKET)
            num_token = expect(TokenType.NUMBER)
            expect(TokenType.RBRACKET)
            expect(TokenType.RBRACE)
            return TagNode(name=name_token.string, index=int(num_token.string))
        
        def parse_method_expr() -> MethodNode:
            name_token = expect(TokenType.METHOD)
            spec = self.methods[name_token.string]

            expect(TokenType.LPAREN)

            if spec.uses_flat_args:
                items = [parse_tuple_item()]
                skip_whitespace()
                while (t := peek()) is not None and t.type == TokenType.COMMA:
                    advance()
                    skip_whitespace()
                    items.append(parse_tuple_item())
                    skip_whitespace()
                expect(TokenType.RPAREN)
                tuples = [TupleNode(items=items)]
            else:
                tuples = [parse_tuple()]
                skip_whitespace()
                while (t := peek()) is not None and t.type == TokenType.COMMA:
                    advance()
                    skip_whitespace()
                    tuples.append(parse_tuple())
                    skip_whitespace()
                expect(TokenType.RPAREN)

            if len(tuples) < spec.min_args:
                raise ValueError(f"method '{name_token.string}' requires at least {spec.min_args} tuples")

            return MethodNode(name=name_token.string, args=tuples)
        
        def parse_tuple() -> TupleNode:
            expect(TokenType.LPAREN)

            items = [parse_tuple_item()]
            skip_whitespace()
            
            while peek() is not None and peek().type == TokenType.COMMA:
                advance()
                skip_whitespace()
                items.append(parse_tuple_item())
                skip_whitespace()
            expect(TokenType.RPAREN)

            return TupleNode(items=items)
        
        def parse_tuple_item():
            token = peek()
            
            if token is None:
                raise ValueError("unexpected end of input in tuple")
            elif token.type == TokenType.QUOTED:
                advance()
                return QuotedNode(value=token.string)
            elif token.type == TokenType.LBRACE:
                return parse_tag_expr()
            
            raise ValueError(f"unexpected token in tuple: {token}")
        
        while peek() is not None:
            token = peek()

            if token.type == TokenType.LBRACE:
                nodes.append(parse_tag_expr())

            elif token.type == TokenType.METHOD:
                nodes.append(parse_method_expr())
            
            else:
                start = i
                while peek() is not None and peek().type not in (TokenType.LBRACE, TokenType.METHOD):
                    advance()
                text = "".join(t.string for t in tokens[start:i])
                nodes.append(TextNode(value=text))
        
        return nodes