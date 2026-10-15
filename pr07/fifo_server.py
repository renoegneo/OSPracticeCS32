"""ПР-7, п.1: сервер вычислений на двух FIFO. Запуск: python3 fifo_server.py (Ctrl+C — остановка)."""
import os
import signal
from calc import FIFO_REQ, FIFO_RESP, answer


def cleanup():
    for path in (FIFO_REQ, FIFO_RESP):
        try:
            os.unlink(path)
        except FileNotFoundError:
            pass


def on_term(signum, frame):
    raise SystemExit(0)      # исключение «раскручивает» стек → сработает finally → cleanup()


def main():
    signal.signal(signal.SIGTERM, on_term)   # SIGINT (Ctrl+C) Python сам превращает в KeyboardInterrupt
    cleanup()                                # хвосты от аварийного прошлого запуска
    os.mkfifo(FIFO_REQ)
    os.mkfifo(FIFO_RESP)
    print(f"сервер: FIFO созданы ({FIFO_REQ}, {FIFO_RESP}); жду клиентов. Остановка: Ctrl+C", flush=True)
    n = 0
    try:
        while True:                          # одна итерация = один клиентский сеанс
            try:
                with open(FIFO_REQ, "r") as req:         # блокируется, пока клиент не откроет REQ на запись
                    with open(FIFO_RESP, "w") as resp:   # блокируется, пока клиент не откроет RESP на чтение
                        n += 1
                        print(f"сервер: клиент #{n} подключился", flush=True)
                        for line in req:                 # цикл кончится по EOF: клиент закрыл свой конец
                            ans = answer(line)
                            print(f"сервер: {line.strip()!r} -> {ans}", flush=True)
                            resp.write(ans + "\n")
                            resp.flush()                 # без flush ответ застрянет в буфере Python
                        print(f"сервер: клиент #{n} отключился", flush=True)
            except BrokenPipeError:                      # клиент исчез, не дождавшись ответа
                print("сервер: клиент пропал до получения ответа", flush=True)
    except KeyboardInterrupt:
        print("\nсервер: Ctrl+C, завершаюсь", flush=True)
    finally:
        cleanup()                            # требование сдачи: после завершения FIFO не остаётся
        print("сервер: FIFO удалены", flush=True)


if __name__ == "__main__":
    main()
