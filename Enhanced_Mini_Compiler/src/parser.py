from ast_nodes import (
    Program, Declaration, Assignment, Print, Read,
    Number, String, Variable, Unary, Binary,
)


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def current(self):
        return self.tokens[self.pos]

    def eat(self, kind=None):
        token = self.current()
        if kind and token.kind != kind and token.value != kind:
            raise SyntaxError(
                f"Expected {kind}, got {token.kind} ({token.value!r}) "
                f"at line {token.line}, column {token.column}"
            )
        self.pos += 1
        return token

    def parse(self):
        statements = []
        while self.current().kind != "EOF":
            statements.append(self.statement())
        return Program(statements)

    # ── Statements ──────────────────────────────────────────────────────

    def statement(self):
        # read(variable);
        if self.current().kind == "READ":
            self.eat("READ")
            self.eat("(")
            name = self.eat("IDENT").value
            self.eat(")")
            self.eat(";")
            return Read(name)

        # Variable declaration: int x = ...; or string s = ...;
        if self.current().kind in {"INT", "STRING"}:
            type_name = self.eat().value
            name = self.eat("IDENT").value
            initializer = None
            if self.current().value == "=":
                self.eat("OP")
                initializer = self.expression()
            self.eat(";")
            return Declaration(type_name, name, initializer)

        # Assignment: x = ...;
        if self.current().kind == "IDENT":
            name = self.eat("IDENT").value
            op_token = self.eat("OP")
            if op_token.value != "=":
                raise SyntaxError(
                    f"Only '=' assignment is supported, got '{op_token.value}' "
                    f"at line {op_token.line}, column {op_token.column}"
                )
            expr = self.expression()
            self.eat(";")
            return Assignment(name, expr)

        # Print statement: print(...);
        if self.current().kind == "PRINT":
            self.eat("PRINT")
            self.eat("(")
            expr = self.expression()
            self.eat(")")
            self.eat(";")
            return Print(expr)

        token = self.current()
        raise SyntaxError(
            f"Unexpected token {token.value!r} at line {token.line}, "
            f"column {token.column}"
        )

    # ── Expressions (operator‑precedence climbing) ──────────────────────

    def expression(self):
        return self.additive()

    def additive(self):
        node = self.multiplicative()
        while self.current().value in {"+", "-"}:
            op = self.eat("OP").value
            node = Binary(node, op, self.multiplicative())
        return node

    def multiplicative(self):
        node = self.unary()
        while self.current().value in {"*", "/", "%"}:
            op = self.eat("OP").value
            node = Binary(node, op, self.unary())
        return node

    def unary(self):
        if self.current().value in {"+", "-"}:
            op = self.eat("OP").value
            return Unary(op, self.unary())
        return self.primary()

    def primary(self):
        token = self.current()

        if token.kind == "NUMBER":
            self.eat("NUMBER")
            return Number(int(token.value))

        if token.kind == "STRING":
            self.eat("STRING")
            raw = token.value[1:-1]  # strip surrounding quotes
            # Decode standard escape sequences safely
            value = raw.replace("\\n", "\n").replace("\\t", "\t")
            value = value.replace('\\"', '"').replace("\\\\", "\\")
            return String(value)

        if token.kind == "IDENT":
            self.eat("IDENT")
            return Variable(token.value)

        if token.value == "(":
            self.eat("(")
            node = self.expression()
            self.eat(")")
            return node

        raise SyntaxError(
            f"Expected expression, got {token.value!r} at line {token.line}, "
            f"column {token.column}"
        )
