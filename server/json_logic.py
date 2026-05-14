"""
json_logic.py — vendored & patched for Python 3
Original: https://github.com/nadirizr/json-logic-py
Fix: dict.keys() is not subscriptable in Python 3; use list() wrapper.
"""

import sys

if sys.version_info[0] < 3:
    string_types = (str, unicode)  # noqa: F821
    integer_types = (int, long)    # noqa: F821
else:
    string_types = (str,)
    integer_types = (int,)


def if_(*args):
    """Implements the 'if' operator with support for multiple elseif clauses."""
    for i in range(0, len(args) - 1, 2):
        if args[i]:
            return args[i + 1]
    if len(args) % 2:
        return args[-1]
    return None


def soft_equals(a, b):
    """Implements the '==' operator, with type coercion."""
    if isinstance(a, string_types) and isinstance(b, string_types):
        return a == b
    if isinstance(a, bool) or isinstance(b, bool):
        return bool(a) == bool(b)
    try:
        return float(a) == float(b)
    except (TypeError, ValueError):
        return a == b


def hard_equals(a, b):
    """Implements the '===' operator."""
    if type(a) != type(b):
        return False
    return a == b


def less(a, b, *args):
    """Implements the '<' operator with chaining: a < b < c ..."""
    types = set([type(a), type(b)])
    if float in types or int in types:
        try:
            a, b = float(a), float(b)
        except (TypeError, ValueError):
            return False
    result = a < b
    if not args:
        return result
    return result and less(b, *args)


def less_or_equal(a, b, *args):
    return (less(a, b) or soft_equals(a, b)) and (not args or less_or_equal(b, *args))


def greater(a, b, *args):
    return less(b, a) and (not args or greater(b, *args))


def greater_or_equal(a, b, *args):
    return (less(b, a) or soft_equals(a, b)) and (not args or greater_or_equal(b, *args))


def plus(*args):
    return sum(float(a) for a in args)


def minus(*args):
    if len(args) == 1:
        return -args[0]
    return args[0] - sum(args[1:])


def merge(*args):
    ret = []
    for arg in args:
        if isinstance(arg, list):
            ret += arg
        else:
            ret.append(arg)
    return ret


def get_var(data, var_name, default=None):
    """Retrieves a value from data using dot-separated path."""
    if var_name is None or var_name == "":
        return data
    try:
        parts = str(var_name).split(".")
        for part in parts:
            if isinstance(data, dict):
                data = data[part]
            elif isinstance(data, list):
                data = data[int(part)]
            else:
                return default
        return data
    except (KeyError, IndexError, TypeError, ValueError):
        return default


operations = {
    "==":  lambda a, b: soft_equals(a, b),
    "===": lambda a, b: hard_equals(a, b),
    "!=":  lambda a, b: not soft_equals(a, b),
    "!==": lambda a, b: not hard_equals(a, b),
    ">":   lambda a, b: greater(a, b),
    ">=":  lambda a, b: greater_or_equal(a, b),
    "<":   less,
    "<=":  less_or_equal,
    "!":   lambda a: not a,
    "!!":  lambda a: bool(a),
    "%":   lambda a, b: a % b,
    "and": lambda *args: next((a for a in args if not a), args[-1]) if args else None,
    "or":  lambda *args: next((a for a in args if a), args[-1]) if args else None,
    "?:":  lambda a, b, c: b if a else c,
    "if":  if_,
    "log": lambda a: (print(a, file=sys.stderr), a)[1],
    "+":   plus,
    "*":   lambda *args: __import__('functools').reduce(lambda x, y: float(x) * float(y), args),
    "-":   minus,
    "/":   lambda a, b: float(a) / float(b),
    "min": lambda *args: min(args),
    "max": lambda *args: max(args),
    "merge": merge,
    "in":  lambda a, b: a in b if b else False,
    "cat": lambda *args: "".join(str(a) for a in args),
    "substr": lambda a, b, *args: a[b:] if not args else a[b:b + args[0]],
}


def jsonLogic(tests, data=None):
    """Evaluates a jsonLogic rule against data."""
    # Primitives — stop recursing
    if tests is None or not isinstance(tests, dict):
        return tests

    data = data or {}

    op = list(tests.keys())[0]   # ← Python 3 fix: wrap in list()
    values = tests[op]

    # --- Data access ---
    if op == "var":
        if isinstance(values, list):
            var_name = values[0]
            default = values[1] if len(values) > 1 else None
        else:
            var_name = values
            default = None
        return get_var(data, var_name, default)

    if op == "missing":
        if not isinstance(values, list):
            values = [values]
        return [v for v in values if get_var(data, v) is None]

    if op == "missing_some":
        need_count, options = values
        missing = jsonLogic({"missing": options}, data)
        return missing if len(missing) >= need_count else []

    # --- Array operations (higher-order) ---
    if op == "filter":
        arr = jsonLogic(values[0], data) if isinstance(values[0], dict) else values[0]
        if isinstance(arr, list):
            return [item for item in arr if jsonLogic(values[1], item)]
        return []

    if op == "map":
        arr = jsonLogic(values[0], data) if isinstance(values[0], dict) else values[0]
        if isinstance(arr, list):
            return [jsonLogic(values[1], item) for item in arr]
        return []

    if op == "reduce":
        arr = jsonLogic(values[0], data) if isinstance(values[0], dict) else values[0]
        if not isinstance(arr, list):
            return values[2] if len(values) > 2 else None
        acc = values[2] if len(values) > 2 else None
        for item in arr:
            acc = jsonLogic(values[1], {"current": item, "accumulator": acc})
        return acc

    if op == "all":
        arr = jsonLogic(values[0], data) if isinstance(values[0], dict) else values[0]
        if not isinstance(arr, list) or not arr:
            return False
        return all(jsonLogic(values[1], item) for item in arr)

    if op == "some":
        arr = jsonLogic(values[0], data) if isinstance(values[0], dict) else values[0]
        if not isinstance(arr, list):
            return False
        return any(jsonLogic(values[1], item) for item in arr)

    if op == "none":
        arr = jsonLogic(values[0], data) if isinstance(values[0], dict) else values[0]
        if not isinstance(arr, list):
            return True
        return not any(jsonLogic(values[1], item) for item in arr)

    # --- Recursive evaluation for standard ops ---
    if not isinstance(values, list):
        values = [values]

    values = [jsonLogic(v, data) for v in values]

    if op in operations:
        return operations[op](*values)  # type: ignore

    raise ValueError(f"Unrecognized operation: {op!r}")