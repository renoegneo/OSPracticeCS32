"""ПР-7, п.2: сервер вычислений на Unix-сокете, поток на клиента. Запуск: python3 sock_server.py"""
import os
import signal
import socket
import threading
from calc import SOCK_PATH, answer

BACKLOG = 8     # ручка: длина очереди ещё не принятых (accept) подключений
_log_lock = threading.Lock()


def log(msg):
    # print из нескольких потоков может смешать строки — печатаем под замком
    with _log_lock:
        print(msg, flush=True)


def serve(conn, cid):
    log(f"сервер: клиент #{cid} подключился")
    try:
        with conn, conn.makefile("rw", encoding="utf-8") as f:   # makefile: читаем/пишем строками, как файл
            for line in f:                                       # EOF = клиент закрыл соединение
                ans = answer(line)
                log(f"сервер: [#{cid}] {line.strip()!r} -> {ans}")
                f.write(ans + "\n")
                f.flush()
    except (BrokenPipeError, ConnectionResetError):
        log(f"сервер: клиент #{cid} оборвал соединение")
    log(f"сервер: клиент #{cid} отключился")


def on_term(signum, frame):
    raise SystemExit(0)


def cleanup():
    try:
        os.unlink(SOCK_PATH)
    except FileNotFoundError:
        pass


def main():
    signal.signal(signal.SIGTERM, on_term)
    cleanup()    # файл сокета от прошлого запуска мешает bind() («Address already in use»)
    srv = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    srv.bind(SOCK_PATH)
    srv.listen(BACKLOG)
    log(f"сервер: слушаю {SOCK_PATH}. Остановка: Ctrl+C")
    cid = 0
    try:
        while True:
            conn, _ = srv.accept()
            cid += 1
            threading.Thread(target=serve, args=(conn, cid), daemon=True).start()
    except KeyboardInterrupt:
        log("\nсервер: Ctrl+C, завершаюсь")
    finally:
        srv.close()
        cleanup()
        log("сервер: файл сокета удалён")


if __name__ == "__main__":
    main()
