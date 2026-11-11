import ast
import operator

BINOPS = {
    "+": operator.add,
    "-": operator.sub,
    "*": operator.mul,
    "/": operator.floordiv,
    "%": operator.mod,
}


def is_int_literal(value):
    try:
        int(value)
        return str(int(value)) == value
    except (ValueError, TypeError):
        return False


def is_literal(value):
    if not isinstance(value, str):
        return False
    if is_int_literal(value):
        return True
    if (value.startswith("'") and value.endswith("'")) or (
        value.startswith('"') and value.endswith('"')
    ):
        return True
    return False


def optimize(instructions):
    code = [tuple(x) for x in instructions]

    # ── Pass 1: Constant & Copy Propagation + Constant Folding ─────────
    constants = {}
    folded = []
    for op, a, b, result in code:
        if op == "print":
            folded.append((op, constants.get(a, a), b, result))
            continue
        if op == "read":
            constants.pop(a, None)
            # Any cached variable that was copied from `a` should be invalidated
            constants = {k: v for k, v in constants.items() if v != a}
            folded.append((op, a, b, result))
            continue

        a = constants.get(a, a)
        b = constants.get(b, b)

        if op == "=":
            if is_literal(a):
                constants[result] = a
            else:
                # Copy propagation for variable aliases
                constants[result] = a
            folded.append((op, a, b, result))
        elif op == "neg" and is_int_literal(a):
            value = str(-int(a))
            constants[result] = value
            folded.append(("=", value, "", result))
        elif op in BINOPS and is_int_literal(a) and is_int_literal(b):
            x, y = int(a), int(b)
            if op in {"/", "%"} and y == 0:
                folded.append((op, a, b, result))
                constants.pop(result, None)
            else:
                value = str(BINOPS[op](x, y))
                constants[result] = value
                folded.append(("=", value, "", result))
        else:
            constants.pop(result, None)
            # Invalidate any mappings where old result was the source
            constants = {k: v for k, v in constants.items() if v != result}
            folded.append((op, a, b, result))

    # ── Pass 2: Common Subexpression Elimination (CSE) ─────────────────
    available = {}
    cse = []
    for op, a, b, result in folded:
        if op in BINOPS:
            key = (op, a, b)
            if key in available:
                cse.append(("=", available[key], "", result))
            else:
                available[key] = result
                cse.append((op, a, b, result))
        else:
            cse.append((op, a, b, result))
            if op == "=":
                # Invalidate expressions using this modified variable
                available = {
                    k: v
                    for k, v in available.items()
                    if k[1] != result and k[2] != result
                }

    # ── Pass 3: Strength Reduction (multiply by power of two -> left shift)
    strength = []
    for op, a, b, result in cse:
        if op == "*" and (is_int_literal(a) or is_int_literal(b)):
            constant = int(a) if is_int_literal(a) else int(b)
            variable = b if is_int_literal(a) else a
            if constant > 0 and constant & (constant - 1) == 0:
                shift = constant.bit_length() - 1
                strength.append(("<<", variable, str(shift), result))
                continue
        strength.append((op, a, b, result))

    # ── Pass 4: Dead Code Elimination ──────────────────────────────────
    live = set()
    kept_reversed = []
    for op, a, b, result in reversed(strength):
        if op == "print":
            if a and not is_literal(a):
                live.add(a)
            kept_reversed.append((op, a, b, result))
        elif op == "read":
            live.discard(a)
            kept_reversed.append((op, a, b, result))
        else:
            if result in live:
                live.discard(result)
                if a and not is_literal(a):
                    live.add(a)
                if b and not is_literal(b):
                    live.add(b)
                kept_reversed.append((op, a, b, result))

    return list(reversed(kept_reversed))
