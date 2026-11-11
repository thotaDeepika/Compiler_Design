import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))
from main import compile_source


def execute_with_input(instructions, input_value):
    """Run the interpreter with a mocked input() that returns input_value."""
    import builtins
    from interpreter import execute

    original_input = builtins.input
    builtins.input = lambda prompt="": str(input_value)
    try:
        return execute(instructions)
    finally:
        builtins.input = original_input


class CompilerTests(unittest.TestCase):
    def test_constant_folding(self):
        result = compile_source("int x = 5 + 3; print(x);")
        self.assertEqual(result["output"], ["8"])

    def test_string_concatenation(self):
        result = compile_source('string s = "Hi"; print(s + " there");')
        self.assertEqual(result["output"], ["Hi there"])

    def test_common_subexpression_and_strength_reduction(self):
        source = "int x; read(x); int a = x * 8; int b = x * 8; print(a + b);"
        from lexer import tokenize
        from parser import Parser
        from semantic import SemanticAnalyzer
        from tac import TACGenerator
        from optimizer import optimize

        tokens = tokenize(source)
        program = Parser(tokens).parse()
        SemanticAnalyzer().analyze(program)
        tac = TACGenerator().generate(program)
        optimized = optimize(tac)

        # Strength reduction should have replaced * 8 with << 3
        self.assertTrue(any(item[0] == "<<" for item in optimized))
        # CSE should have reused the first computation via an assignment
        self.assertTrue(
            any(item[0] == "=" and item[1].startswith("t") for item in optimized)
        )

        output, _ = execute_with_input(optimized, 3)
        self.assertEqual(output, ["48"])

    def test_undeclared_variable(self):
        with self.assertRaises(NameError):
            compile_source("int x = y + 1; print(x);")


if __name__ == "__main__":
    unittest.main()

