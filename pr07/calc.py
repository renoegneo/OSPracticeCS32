"""ПР-7: общее для FIFO- и сокет-сервисов — безопасный калькулятор, пути, эталонные тесты."""
import ast
import operator

FIFO_REQ = "/tmp/pr07_req"      # ручка: FIFO «клиент → сервер»
FIFO_RESP = "/tmp/pr07_resp"    # ручка: FIFO «сервер → клиент»
SOCK_PATH = "/tmp/pr07.sock"    # ручка: путь Unix-сокета
MAX_POW = 100       # ручка: макс. степень (защита от 9**9**9, которое «повесит» сервер)
MAX_BITS = 10_000   # ручка: макс. размер целого результата в битах (защита от разрастания)
MAX_LEN = 200       # ручка: макс. длина выражения

_BIN = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
        ast.Div: operator.truediv, ast.FloorDiv: operator.floordiv,
        ast.Mod: operator.mod, ast.Pow: operator.pow}
_UN = {ast.UAdd: operator.pos, ast.USub: operator.neg}


def _ev(node):
    # Белый список: разрешено только то, что перечислено; всё остальное — отказ.
    if isinstance(node, ast.Expression):
        return _ev(node.body)
    if isinstance(node, ast.Constant) and type(node.value) in (int, float):
        return node.value                       # type(...) in (...), а не isinstance: True/False не пройдут
    if isinstance(node, ast.UnaryOp) and type(node.op) in _UN:
        return _UN[type(node.op)](_ev(node.operand))
    if isinstance(node, ast.BinOp) and type(node.op) in _BIN:
        left, right = _ev(node.left), _ev(node.right)
        if isinstance(node.op, ast.Pow) and abs(right) > MAX_POW:
            raise ValueError(f"степень больше {MAX_POW}")
        res = _BIN[type(node.op)](left, right)
        if isinstance(res, int) and res.bit_length() > MAX_BITS:
            raise ValueError("результат слишком большой")
        return res
    raise ValueError("недопустимый элемент выражения")


def safe_eval(expr):
    if len(expr) > MAX_LEN:
        raise ValueError(f"выражение длиннее {MAX_LEN} символов")
    return _ev(ast.parse(expr, mode="eval"))


def answer(line):
    """Строка-запрос -> строка-ответ: 'OK значение' или 'ERR причина'. Никогда не бросает исключений."""
    try:
        return f"OK {safe_eval(line.strip())}"
    except ZeroDivisionError:
        return "ERR деление на ноль"
    except (ValueError, SyntaxError, ArithmeticError, RecursionError, MemoryError) as e:
        return f"ERR {e}"


# Эталонные пары (выражение, ожидаемый ответ) — считал руками, не программой:
TESTS = [
    ("2+3*4", "OK 14"),                 # умножение раньше сложения: 3*4=12, 2+12=14
    ("(1+2)*(3+4)", "OK 21"),           # 3*7
    ("2**10", "OK 1024"),
    ("100/8", "OK 12.5"),               # «/» всегда даёт float
    ("17%5", "OK 2"),                   # 17 = 3*5 + 2
    ("7//2", "OK 3"),                   # целочисленное деление
    ("-5+2", "OK -3"),
    ("10/0", "ERR деление на ноль"),
    ("__import__('os')", "ERR недопустимый элемент выражения"),   # то, от чего спасает отказ от eval
]
