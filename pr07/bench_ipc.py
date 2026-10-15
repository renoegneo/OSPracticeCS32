"""ПР-7, п.3–4: 10^7 чисел (int64, 80 МБ) между процессами: Pipe / FIFO / AF_UNIX / shared_memory."""
import hashlib
import multiprocessing as mp
import os
import socket
import statistics
import time
from array import array
from multiprocessing import shared_memory

N = 10**7                 # ручка: сколько чисел передаём
NBYTES = N * 8            # 'q' = int64 = 8 байт: 10^7 * 8 = 80 000 000 Б
RUNS = 3                  # ручка: число повторов (берём медиану)
CHUNK = 1 << 20           # ручка: размер куска для FIFO/сокета (1 МиБ)
TIMEOUT = 60              # ручка: сколько ждём ребёнка, сек (чтобы сбой не вешал терминал)
FIFO_PATH = "/tmp/pr07_bench.fifo"
SOCK_PATH = "/tmp/pr07_bench.sock"
SHM_NAME = "pr07_shm"


# ---------- общие помощники ----------
def _recv_into(read_some, buf):
    """Читает в ГОТОВЫЙ буфер, пока не заполнит или не придёт EOF. Возвращает число прочитанных байт."""
    mv = memoryview(buf)
    pos = 0
    while pos < len(buf):
        n = read_some(mv[pos:pos + CHUNK])
        if n == 0:                       # EOF раньше времени
            break
        pos += n
    return pos


def wait_res(res, what):
    if not res.poll(TIMEOUT):
        raise TimeoutError(f"{what}: ребёнок не ответил за {TIMEOUT} с")
    return res.recv()                    # если ребёнок умер, здесь будет EOFError, а не вечное ожидание


def reap(p):
    p.join(TIMEOUT)
    if p.is_alive():
        p.terminate()
        p.join()


# ---------- дочерние процессы: «получил → сразу сказал got → потом посчитал sha256» ----------
def child_pipe(conn, ready, res):
    ready.set()
    buf = conn.recv_bytes()
    res.send("got")
    res.send(hashlib.sha256(buf).hexdigest())


def child_fifo(ready, res):
    buf = bytearray(NBYTES)              # память выделяем ДО сигнала ready — не попадает в замер
    ready.set()
    fd = os.open(FIFO_PATH, os.O_RDONLY)     # блокируется, пока родитель не откроет на запись
    try:
        pos = _recv_into(lambda m: os.readv(fd, [m]), buf)
    finally:
        os.close(fd)
    res.send("got" if pos == NBYTES else f"short {pos}")
    res.send(hashlib.sha256(buf).hexdigest())


def child_sock(ready, res):
    buf = bytearray(NBYTES)
    ready.set()
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
        s.connect(SOCK_PATH)
        pos = _recv_into(s.recv_into, buf)
    res.send("got" if pos == NBYTES else f"short {pos}")
    res.send(hashlib.sha256(buf).hexdigest())


def child_shm(ready, go, res):
    ready.set()
    go.wait(TIMEOUT)                     # Event — это и есть синхронизация, которую пишет программист
    shm = shared_memory.SharedMemory(name=SHM_NAME)      # подключились к готовому сегменту
    res.send("got")
    view = shm.buf[:NBYTES]
    digest = hashlib.sha256(view).hexdigest()
    view.release()                       # без release() close() ругнётся на «exported pointers»
    shm.close()
    res.send(digest)


# ---------- родительская сторона: возвращает (время, корректно?, время записи в shm или None) ----------
def bench_pipe(ctx, raw, want):
    ready = ctx.Event()
    res_r, res_w = ctx.Pipe(duplex=False)
    rx, tx = ctx.Pipe(duplex=False)      # duplex=False => настоящий os.pipe(); tx пишет родитель, rx читает ребёнок
    p = ctx.Process(target=child_pipe, args=(rx, ready, res_w))
    p.start()
    rx.close()                           # в родителе закрываем то, чем он не пользуется
    res_w.close()
    try:
        ready.wait(TIMEOUT)
        t0 = time.perf_counter()
        tx.send_bytes(raw)
        status = wait_res(res_r, "pipe")
        t1 = time.perf_counter()
        digest = wait_res(res_r, "pipe")
    finally:
        tx.close()
        reap(p)
    return t1 - t0, status == "got" and digest == want, None


def bench_fifo(ctx, raw, want):
    if os.path.exists(FIFO_PATH):
        os.unlink(FIFO_PATH)
    os.mkfifo(FIFO_PATH)
    ready = ctx.Event()
    res_r, res_w = ctx.Pipe(duplex=False)
    p = ctx.Process(target=child_fifo, args=(ready, res_w))
    p.start()
    res_w.close()
    fd = None
    try:
        ready.wait(TIMEOUT)
        fd = os.open(FIFO_PATH, os.O_WRONLY)     # блокируется, пока ребёнок не откроет на чтение
        t0 = time.perf_counter()
        pos = 0
        while pos < NBYTES:
            pos += os.write(fd, raw[pos:pos + CHUNK])    # write может записать меньше — считаем фактическое
        os.close(fd)
        fd = None
        status = wait_res(res_r, "fifo")
        t1 = time.perf_counter()
        digest = wait_res(res_r, "fifo")
    finally:
        if fd is not None:
            os.close(fd)
        reap(p)
        os.unlink(FIFO_PATH)
    return t1 - t0, status == "got" and digest == want, None


def bench_sock(ctx, raw, want):
    if os.path.exists(SOCK_PATH):
        os.unlink(SOCK_PATH)
    srv = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    srv.bind(SOCK_PATH)
    srv.listen(1)
    srv.settimeout(TIMEOUT)
    ready = ctx.Event()
    res_r, res_w = ctx.Pipe(duplex=False)
    p = ctx.Process(target=child_sock, args=(ready, res_w))
    p.start()
    res_w.close()
    conn = None
    try:
        ready.wait(TIMEOUT)
        conn, _ = srv.accept()
        t0 = time.perf_counter()
        conn.sendall(raw)
        status = wait_res(res_r, "socket")
        t1 = time.perf_counter()
        digest = wait_res(res_r, "socket")
    finally:
        if conn is not None:
            conn.close()
        srv.close()
        reap(p)
        os.unlink(SOCK_PATH)
    return t1 - t0, status == "got" and digest == want, None


def bench_shm(ctx, raw, want):
    try:                                 # хвост от аварийного запуска мешает create=True
        old = shared_memory.SharedMemory(name=SHM_NAME)
        old.close()
        old.unlink()
    except FileNotFoundError:
        pass
    ready, go = ctx.Event(), ctx.Event()
    res_r, res_w = ctx.Pipe(duplex=False)
    p = ctx.Process(target=child_shm, args=(ready, go, res_w))
    p.start()
    res_w.close()
    shm = None
    try:
        ready.wait(TIMEOUT)
        t0 = time.perf_counter()
        shm = shared_memory.SharedMemory(name=SHM_NAME, create=True, size=NBYTES)
        shm.buf[:NBYTES] = raw           # одно копирование (memcpy) в общую память
        t_write = time.perf_counter() - t0
        go.set()                         # «данные готовы, можно подключаться»
        status = wait_res(res_r, "shm")
        t1 = time.perf_counter()
        digest = wait_res(res_r, "shm")
    finally:
        reap(p)
        if shm is not None:
            shm.close()
            shm.unlink()                 # удаляет сегмент из /dev/shm — только владелец, один раз
    return t1 - t0, status == "got" and digest == want, t_write


def main():
    ctx = mp.get_context("spawn")
    print(f"готовлю {N:,} чисел int64 = {NBYTES:,} Б ...", flush=True)
    data = array("q", range(N))
    raw = memoryview(data).cast("B")     # тот же буфер как байты, без копирования
    want = hashlib.sha256(raw).hexdigest()

    benches = [("Pipe (os.pipe)", bench_pipe), ("FIFO (mkfifo)", bench_fifo),
               ("Unix-сокет (AF_UNIX)", bench_sock), ("shared_memory", bench_shm)]
    rows, all_ok = [], True
    for name, fn in benches:
        times, writes = [], []
        for i in range(RUNS):
            t, ok, wr = fn(ctx, raw, want)
            all_ok &= ok
            times.append(t)
            if wr is not None:
                writes.append(wr)
            extra = f", из них запись в shm {wr:.3f} с" if wr is not None else ""
            print(f"{name}: прогон {i + 1}: {t:.3f} с{extra}, данные {'совпали' if ok else 'НЕ СОВПАЛИ'}", flush=True)
        med = statistics.median(times)
        rows.append((name, med, NBYTES / med / 1e6, statistics.median(writes) if writes else None))

    print("\n| Механизм | Медиана, с | Скорость, МБ/с |")
    print("|---|---|---|")
    for name, med, speed, wr in rows:
        print(f"| {name} | {med:.3f} | {speed:.0f} |")
    for name, med, speed, wr in rows:
        if wr is not None:
            print(f"\n{name}: на запись в сегмент ушло {wr:.3f} с из {med:.3f} с (остальное — создание и подключение)")
    print("\nРЕЗУЛЬТАТ:", "OK" if all_ok else "FAIL")


if __name__ == "__main__":      # обязательно: spawn заново импортирует этот файл в каждом ребёнке
    main()
