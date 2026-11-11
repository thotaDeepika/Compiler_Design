from dataclasses import dataclass
from typing import Any, List, Optional


@dataclass
class Program:
    statements: List[Any]


@dataclass
class Declaration:
    type_name: str
    name: str
    initializer: Optional[Any] = None


@dataclass
class Assignment:
    name: str
    expression: Any


@dataclass
class Print:
    expression: Any


@dataclass
class Number:
    value: int


@dataclass
class String:
    value: str


@dataclass
class Variable:
    name: str


@dataclass
class Unary:
    operator: str
    operand: Any


@dataclass
class Binary:
    left: Any
    operator: str
    right: Any


@dataclass
class Read:
    name: str
