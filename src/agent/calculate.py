"""calculate tool: exact arithmetic, never delegated to the LLM (README §1).

Parses via `ast` and only evaluates a whitelist of safe nodes (numbers,
+ - * / and unary minus) — never Python's `eval()`, which would execute
arbitrary code from LLM-controlled input.
"""
import ast

_ALLOWED_BINOPS = {
    ast.Add: lambda a, b: a + b,
    ast.Sub: lambda a, b: a - b,
    ast.Mult: lambda a, b: a * b,
    ast.Div: lambda a, b: a / b,
}


def _eval_node(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp):
        op = _ALLOWED_BINOPS.get(type(node.op))
        if op is None:
            raise ValueError(f"opérateur non autorisé : {type(node.op).__name__}")
        return op(_eval_node(node.left), _eval_node(node.right))
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        return -_eval_node(node.operand)
    raise ValueError(f"expression non autorisée : {type(node).__name__}")


def calculate(expression: str) -> float:
    try:
        tree = ast.parse(expression, mode="eval")
    except SyntaxError as exc:
        raise ValueError(f"expression invalide : {expression!r}") from exc
    try:
        return _eval_node(tree.body)
    except ZeroDivisionError as exc:
        raise ValueError("division par zéro") from exc
