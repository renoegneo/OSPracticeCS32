"""ПР-6: общий код — кольцевой буфер, производители/потребители, проверки."""
import random
import threading
import time
from collections import Counter

N_ITEMS = 1000   # ручка: сколько элементов всего
CAP = 5          # ручка: размер кольцевого буфера
N_PROD = 3       # ручка: число производителей
N_CONS = 2       # ручка: число потребителей
JITTER = 0.0     # ручка: макс. случайная пауза (сек) — перемешивает чередование потоков
TIMEOUT = 10     # ручка: сколько ждать потоки (сек), чтобы сломанная версия не повесила терминал
STOP = -1        # «ядовитая таблетка»: сигнал потребителю «заканчивай»


class Ring:
    """Кольцевой буфер БЕЗ синхронизации + проверка инвариантов.

    Инвариант: 0 <= count <= CAP. Методы _put_raw/_get_raw вызывать
    ТОЛЬКО внутри критической секции (участка кода, где одновременно
    может быть один поток). Нарушения не роняют программу, а логируются.
    """

    def __init__(self, cap=CAP):
        self.cap = cap
        self.slots = [None] * cap
        self.head = 0      # откуда читаем
        self.tail = 0      # куда пишем
        self.count = 0     # сколько элементов лежит сейчас
        self.violations = []

    def _put_raw(self, item):
        if self.count >= self.cap:
            self.violations.append(f"ПЕРЕПОЛНЕНИЕ: put({item}) при count={self.count}")
            return
        self.slots[self.tail] = item
        self.tail = (self.tail + 1) % self.cap   # % — «замыкаем» индекс в кольцо
        self.count += 1

    def _get_raw(self):
        if self.count <= 0:
            self.violations.append("ЧТЕНИЕ ИЗ ПУСТОГО буфера")
            return None
        item = self.slots[self.head]
        self.slots[self.head] = None   # стираем: повторное чтение сразу вылезет как None
        self.head = (self.head + 1) % self.cap
        self.count -= 1
        return item


def _pause():
    if JITTER:
        time.sleep(random.random() * JITTER)


def producer(buf, pid):
    # pid, pid+N_PROD, pid+2*N_PROD, ... — у каждого производителя свои номера, пересечений нет
    for item in range(pid, N_ITEMS, N_PROD):
        _pause()
        buf.put(item)


def consumer(buf, out):
    # out — СВОЙ список у каждого потребителя: общих данных нет, значит, и замок не нужен
    while True:
        _pause()
        item = buf.get()
        if item == STOP or item is None:
            break
        out.append(item)


def run_test(buf, title):
    """Запускает 3 производителей + 2 потребителей, проверяет инварианты."""
    outs = [[] for _ in range(N_CONS)]
    prods = [threading.Thread(target=producer, args=(buf, i), daemon=True, name=f"P{i}")
             for i in range(N_PROD)]
    cons = [threading.Thread(target=consumer, args=(buf, outs[i]), daemon=True, name=f"C{i}")
            for i in range(N_CONS)]
    # daemon=True: если поток завис, программа всё равно сможет выйти

    t0 = time.perf_counter()
    for t in prods + cons:
        t.start()
    for t in prods:
        t.join(TIMEOUT)

    # STOP кладём из отдельного потока: в сломанных версиях put может зависнуть
    stopper = threading.Thread(target=lambda: [buf.put(STOP) for _ in range(N_CONS)],
                               daemon=True, name="stopper")
    stopper.start()
    stopper.join(TIMEOUT)
    for t in cons:
        t.join(TIMEOUT)
    elapsed = time.perf_counter() - t0

    # --- проверки: всё считаем ПОСЛЕ join, в главном потоке ---
    flat = [x for o in outs for x in o]
    dups = {k: v for k, v in Counter(flat).items() if v > 1}
    missing = sorted(set(range(N_ITEMS)) - set(flat))
    hung = [t.name for t in prods + cons + [stopper] if t.is_alive()]

    print(f"=== {title} ===")
    print(f"время:            {elapsed:.3f} с")
    print(f"потреблено всего: {len(flat)} (" +
          ", ".join(f"потребитель {i}: {len(o)}" for i, o in enumerate(outs)) + ")")
    print(f"дубликатов:       {len(dups)}")
    if dups:
        print("   примеры:", list(dups.items())[:5])
    print(f"потеряно:         {len(missing)}")
    if missing:
        print("   примеры:", missing[:5])
    print(f"нарушений буфера: {len(buf.violations)}")
    for v in buf.violations[:5]:
        print("   ", v)
    print(f"буфер в конце:    count={buf.count}")
    print(f"зависших потоков: {len(hung)} {hung if hung else ''}")

    ok = not dups and not missing and not buf.violations and buf.count == 0 and not hung
    print("РЕЗУЛЬТАТ:", "OK" if ok else "FAIL")
    return ok
