import ast


def atom(value, memory):
    """Resolve a TAC operand to its runtime value."""
    if value in memory:
        return memory[value]
    if (value.startswith("'") and value.endswith("'")) or (
        value.startswith('"') and value.endswith('"')
    ):
        return ast.literal_eval(value)
    try:
        return int(value)
    except ValueError:
        raise RuntimeError(f"Unknown TAC operand: {value}")


def execute(instructions):
    memory = {}
    output = []
    for op, a, b, result in instructions:
        if op == "read":
            prompt = f"Enter value for {a}: "
            val = input(prompt)
            memory[a] = int(val.strip())
        elif op == "=":
            memory[result] = atom(a, memory)
        elif op == "neg":
            memory[result] = -atom(a, memory)
        elif op == "<<":
            memory[result] = atom(a, memory) << atom(b, memory)
        elif op in {"+", "-", "*", "/", "%"}:
            x, y = atom(a, memory), atom(b, memory)
            if op == "+":
                value = x + y
            elif op == "-":
                value = x - y
            elif op == "*":
                value = x * y
            elif op == "/":
                if y == 0:
                    raise ZeroDivisionError("Division by zero at runtime")
                value = x // y
            elif op == "%":
                if y == 0:
                    raise ZeroDivisionError("Modulo by zero at runtime")
                value = x % y
            memory[result] = value
        elif op == "print":
            output.append(str(atom(a, memory)))
        else:
            raise RuntimeError(f"Unsupported TAC operation: {op}")
    return output, memory
