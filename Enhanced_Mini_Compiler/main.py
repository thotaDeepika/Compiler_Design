import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

# pyrefly: ignore[missing-import]
from lexer import tokenize
# pyrefly: ignore[missing-import]
from parser import Parser
# pyrefly: ignore[missing-import]
from semantic import SemanticAnalyzer
# pyrefly: ignore[missing-import]
from tac import TACGenerator, format_tac
# pyrefly: ignore[missing-import]
from optimizer import optimize
# pyrefly: ignore[missing-import]
from interpreter import execute


def compile_source(source):
    tokens = tokenize(source)
    ast = Parser(tokens).parse()
    symbols = SemanticAnalyzer().analyze(ast)
    generator = TACGenerator()
    original_tac = generator.generate(ast)
    optimized_tac = optimize(original_tac)
    output, memory = execute(optimized_tac)
    return {
        "tokens": tokens,
        "symbols": symbols,
        "original_tac": original_tac,
        "optimized_tac": optimized_tac,
        "output": output,
        "memory": memory,
    }


def main():
    if len(sys.argv) > 1:
        source = Path(sys.argv[1]).read_text(encoding="utf-8")
    else:
        print(
            "Enter your program. Finish with Ctrl+D (Linux/macOS) "
            "or Ctrl+Z then Enter (Windows):"
        )
        source = sys.stdin.read()

    try:
        result = compile_source(source)

        print("\n=== SYMBOL TABLE ===")
        for name, info in result["symbols"].items():
            print(f"{name}: {info['type']}")

        print("\n=== TAC BEFORE OPTIMIZATION ===")
        before = format_tac(result["original_tac"])
        print("\n".join(before) if before else "(empty)")

        print("\n=== TAC AFTER OPTIMIZATION ===")
        after = format_tac(result["optimized_tac"])
        print("\n".join(after) if after else "(empty)")

        removed = len(result["original_tac"]) - len(result["optimized_tac"])
        reduction = (
            (removed / len(result["original_tac"]) * 100)
            if result["original_tac"]
            else 0
        )
        print(f"\nInstruction count: {len(before)} -> {len(after)}")
        print(f"Instruction reduction: {reduction:.1f}%")

        print("\n=== PROGRAM OUTPUT ===")
        print("\n".join(result["output"]) if result["output"] else "(no output)")

    except Exception as exc:
        print(f"Compiler error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

