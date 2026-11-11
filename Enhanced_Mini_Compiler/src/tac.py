from ast_nodes import (
    Program, Declaration, Assignment, Print, Read,
    Number, String, Variable, Unary, Binary,
)


class TACGenerator:
    def __init__(self):
        self.instructions = []
        self.temp_count = 0

    def temp(self):
        self.temp_count += 1
        return f"t{self.temp_count}"

    def generate(self, program):
        for stmt in program.statements:
            if isinstance(stmt, Declaration):
                if stmt.initializer is not None:
                    value = self.expression(stmt.initializer)
                    self.instructions.append(("=", value, "", stmt.name))
            elif isinstance(stmt, Assignment):
                value = self.expression(stmt.expression)
                self.instructions.append(("=", value, "", stmt.name))
            elif isinstance(stmt, Print):
                value = self.expression(stmt.expression)
                self.instructions.append(("print", value, "", ""))
            elif isinstance(stmt, Read):
                self.instructions.append(("read", stmt.name, "", ""))
        return list(self.instructions)

    def expression(self, node):
        if isinstance(node, Number):
            return str(node.value)
        if isinstance(node, String):
            return repr(node.value)
        if isinstance(node, Variable):
            return node.name
        if isinstance(node, Unary):
            value = self.expression(node.operand)
            if node.operator == "+":
                return value
            result = self.temp()
            self.instructions.append(("neg", value, "", result))
            return result
        if isinstance(node, Binary):
            left = self.expression(node.left)
            right = self.expression(node.right)
            result = self.temp()
            self.instructions.append((node.operator, left, right, result))
            return result
        raise TypeError(f"Unknown AST node: {type(node).__name__}")


def format_tac(instructions):
    """Convert TAC tuples into human-readable strings."""
    lines = []
    for op, a, b, result in instructions:
        if op == "print":
            lines.append(f"print {a}")
        elif op == "read":
            lines.append(f"read {a}")
        elif op == "=":
            lines.append(f"{result} = {a}")
        elif op == "neg":
            lines.append(f"{result} = -{a}")
        else:
            lines.append(f"{result} = {a} {op} {b}")
    return lines
