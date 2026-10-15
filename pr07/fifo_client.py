"""ПР-7, п.1: клиент FIFO-сервера.
python3 fifo_client.py                  — прогнать набор тестов
python3 fifo_client.py "2+2" "3*(4+1)"  — свои выражения
"""
import sys
from calc import FIFO_REQ, FIFO_RESP, TESTS


def main():
    cases = [(e, None) for e in sys.argv[1:]] or TESTS   # None = эталона нет, просто печатаем
    bad = 0
    try:
        with open(FIFO_REQ, "w") as req:          # порядок как у сервера: сначала REQ...
            with open(FIFO_RESP, "r") as resp:    # ...потом RESP (иначе взаимная блокировка)
                for expr, want in cases:
                    req.write(expr + "\n")
                    req.flush()                   # без flush сервер будет ждать строку вечно
                    got = resp.readline().strip()
                    if want is None:
                        mark = ""
                    elif got == want:
                        mark = " [ок]"
                    else:
                        mark = f" [ОШИБКА, ждал {want!r}]"
                        bad += 1
                    print(f"клиент: {expr!r} -> {got!r}{mark}", flush=True)
    except FileNotFoundError:
        sys.exit("клиент: FIFO нет — сервер не запущен? (python3 fifo_server.py в другом терминале)")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
