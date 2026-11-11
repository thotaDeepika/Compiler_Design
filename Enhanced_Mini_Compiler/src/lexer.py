import re
from dataclasses import dataclass


@dataclass
class Token:
    kind: str
    value: str
    line: int
    column: int


TOKEN_RE = re.compile(
    r"(?P<SPACE>[ \t\r]+)|(?P<NEWLINE>\n)|"
    r"(?P<COMMENT>//[^\n]*)|"
    r'(?P<STRING>"(?:\\.|[^"\\])*")|'
    r"(?P<NUMBER>\d+)|"
    r"(?P<IDENT>[A-Za-z_][A-Za-z0-9_]*)|"
    r"(?P<OP>==|!=|<=|>=|<<|[+\-*/%=<>])|"
    r"(?P<PUNCT>[{}();,])"
)

KEYWORDS = {"int", "string", "print", "read"}


def tokenize(source: str):
    tokens = []
    pos, line, col = 0, 1, 1
    while pos < len(source):
        match = TOKEN_RE.match(source, pos)
        if not match:
            raise SyntaxError(
                f"Unexpected character {source[pos]!r} at line {line}, column {col}"
            )
        kind = match.lastgroup
        value = match.group()
        if kind == "NEWLINE":
            line += 1
            col = 1
        else:
            if kind not in {"SPACE", "COMMENT"}:
                if kind == "IDENT" and value in KEYWORDS:
                    kind = value.upper()
                tokens.append(Token(kind, value, line, col))
            col += len(value)
        pos = match.end()
    tokens.append(Token("EOF", "", line, col))
    return tokens
