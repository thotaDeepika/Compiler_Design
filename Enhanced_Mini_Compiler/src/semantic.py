from ast_nodes import (
    Program, Declaration, Assignment, Print, Read,
    Number, String, Variable, Unary, Binary,
)


class SemanticAnalyzer:
    def __init__(self):
        self.symbols = {}

    def analyze(self, program):
        for stmt in program.statements:
            if isinstance(stmt, Declaration):
                if stmt.name in self.symbols:
                    raise TypeError(
                        f"Variable '{stmt.name}' is already declared"
                    )
                self.symbols[stmt.name] = {
                    "type": stmt.type_name,
                    "initialized": False,
                }
                if stmt.initializer is not None:
                    actual = self.expression_type(stmt.initializer)
                    self.check_type(stmt.type_name, actual, stmt.name)
                    self.symbols[stmt.name]["initialized"] = True

            elif isinstance(stmt, Assignment):
                if stmt.name not in self.symbols:
                    raise NameError(
                        f"Variable '{stmt.name}' is not declared"
                    )
                actual = self.expression_type(stmt.expression)
                expected = self.symbols[stmt.name]["type"]
                self.check_type(expected, actual, stmt.name)
                self.symbols[stmt.name]["initialized"] = True

            elif isinstance(stmt, Print):
                self.expression_type(stmt.expression)

            elif isinstance(stmt, Read):
                if stmt.name not in self.symbols:
                    raise NameError(
                        f"Variable '{stmt.name}' is not declared"
                    )
                if self.symbols[stmt.name]["type"] != "int":
                    raise TypeError(
                        "read() currently accepts integer variables only"
                    )
                self.symbols[stmt.name]["initialized"] = True

        return self.symbols

    def check_type(self, expected, actual, name):
        if expected != actual:
            raise TypeError(
                f"Type mismatch for '{name}': expected {expected}, got {actual}"
            )

    def expression_type(self, node):
        if isinstance(node, Number):
            return "int"

        if isinstance(node, String):
            return "string"

        if isinstance(node, Variable):
            if node.name not in self.symbols:
                raise NameError(f"Variable '{node.name}' is not declared")
            if not self.symbols[node.name]["initialized"]:
                raise ValueError(
                    f"Variable '{node.name}' may be used before initialization"
                )
            return self.symbols[node.name]["type"]

        if isinstance(node, Unary):
            typ = self.expression_type(node.operand)
            if typ != "int":
                raise TypeError(
                    "Unary arithmetic operators require integer operands"
                )
            return "int"

        if isinstance(node, Binary):
            left = self.expression_type(node.left)
            right = self.expression_type(node.right)
            # String concatenation with +
            if node.operator == "+" and left == "string" and right == "string":
                return "string"
            if left != "int" or right != "int":
                raise TypeError(
                    f"Operator '{node.operator}' requires integer operands"
                )
            # Compile-time division by zero check
            if node.operator in {"/", "%"}:
                if isinstance(node.right, Number) and node.right.value == 0:
                    raise ZeroDivisionError(
                        f"{'Division' if node.operator == '/' else 'Modulo'} "
                        f"by zero"
                    )
            return "int"

        raise TypeError(f"Unknown expression node: {type(node).__name__}")
