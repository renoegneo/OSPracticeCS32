"""ПР-7, п.2: N клиентов-ПРОЦЕССОВ одновременно. Запуск: python3 sock_client.py [N]"""
import multiprocessing as mp
import os
import socket
import sys
import time
from calc import SOCK_PATH, TESTS

N_CLIENTS = 4     # ручка: сколько клиентов-процессов
N_REQ = 5         # ручка: сколько запросов делает каждый клиент
THINK = 0.2       # ручка: «раздумья» клиента между запросами, сек (чтобы клиенты заведомо пересекались)


def client(cid):
    bad = 0
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
        s.connect(SOCK_PATH)
        with s.makefile("rw", encoding="utf-8") as f:
            for i in range(N_REQ):
                expr, want = TESTS[(cid + i) % len(TESTS)]   # у разных клиентов — разные выражения
                f.write(expr + "\n")
                f.flush()
                got = f.readline().strip()
                ok = got == want
                bad += not ok
                print(f"клиент {cid} (pid {os.getpid()}): {expr!r} -> {got} "
                      f"[{'ок' if ok else 'ОШИБКА, ждал ' + want}]", flush=True)
                time.sleep(THINK)
    raise SystemExit(1 if bad else 0)      # код возврата процесса = итог проверки


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else N_CLIENTS
    if not os.path.exists(SOCK_PATH):
        sys.exit("клиенты: сокета нет — сервер не запущен? (python3 sock_server.py в другом терминале)")
    t0 = time.perf_counter()
    procs = [mp.Process(target=client, args=(i,)) for i in range(n)]
    for p in procs:
        p.start()
    for p in procs:
        p.join()                           # join обязателен: иначе зомби
    elapsed = time.perf_counter() - t0
    codes = [p.exitcode for p in procs]
    print(f"\nкоды возврата клиентов: {codes}")
    print(f"общее время: {elapsed:.2f} с")
    print(f"  параллельно ожидается ≈ N_REQ*THINK = {N_REQ}*{THINK} = {N_REQ * THINK:.1f} с")
    print(f"  если бы сервер обслуживал по очереди ≈ n*N_REQ*THINK = {n}*{N_REQ}*{THINK} = {n * N_REQ * THINK:.1f} с")
    print("РЕЗУЛЬТАТ:", "OK" if all(c == 0 for c in codes) else "FAIL")
    sys.exit(0 if all(c == 0 for c in codes) else 1)


if __name__ == "__main__":
    main()
