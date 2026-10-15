"""ПР-6, п.3: многоразовый барьер на условной переменной, 4 потока × 3 фазы."""
import random
import sys
import threading
import time

N_THREADS = 4     # ручка: число потоков
N_PHASES = 3      # ручка: число фаз
MAX_WORK = 0.05   # ручка: макс. «работа» в фазе (сек), случайная — чтобы потоки приходили в разном порядке


class Barrier:
    def __init__(self, n):
        self.n = n
        self.count = 0              # сколько потоков уже пришло на барьер
        self.generation = 0         # номер «поколения» барьера
        self.cond = threading.Condition()

    def wait(self):
        with self.cond:
            gen = self.generation   # запомнили своё поколение
            self.count += 1
            if self.count == self.n:        # я последний: открываем барьер
                self.count = 0              # сброс — барьер можно использовать в следующей фазе
                self.generation += 1
                self.cond.notify_all()      # будим ВСЕХ (не одного)
            else:
                while gen == self.generation:   # ждём смены поколения, а не «count == n»
                    self.cond.wait()
    # ЗАЧЕМ generation: быстрый поток, пройдя барьер, сразу придёт на него снова (следующая фаза).
    # Условие «count == n» к этому моменту уже сброшено, и спящие потоки могли бы не заметить,
    # что барьер открывался. Номер поколения не сбрасывается, поэтому «открылся» не теряется.
    # Цикл while защищает и от ложных пробуждений (spurious wakeup).


def worker(tid, barrier, events, ev_lock):
    for phase in range(N_PHASES):
        with ev_lock:
            events.append(("start", phase, tid))
        time.sleep(random.random() * MAX_WORK)   # имитация работы
        with ev_lock:
            events.append(("end", phase, tid))
        barrier.wait()


def check(events):
    """Инвариант: ни один поток не начал фазу k+1, пока не закончили ВСЕ потоки фазы k."""
    problems = []
    if len(events) != 2 * N_THREADS * N_PHASES:
        problems.append(f"событий {len(events)}, ожидалось {2 * N_THREADS * N_PHASES}")
        return problems
    for ph in range(N_PHASES - 1):
        last_end = max(i for i, (k, p, _) in enumerate(events) if k == "end" and p == ph)
        first_start = min(i for i, (k, p, _) in enumerate(events) if k == "start" and p == ph + 1)
        if first_start < last_end:
            problems.append(f"фаза {ph + 1} началась (событие #{first_start}) "
                            f"раньше, чем закончилась фаза {ph} (событие #{last_end})")
    return problems


def run(barrier, title):
    events, ev_lock = [], threading.Lock()
    threads = [threading.Thread(target=worker, args=(i, barrier, events, ev_lock),
                                daemon=True, name=f"W{i}") for i in range(N_THREADS)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(10)
    print(f"=== {title} ===")
    for i, (kind, ph, tid) in enumerate(events):   # печать из главного потока после join
        print(f"[{i:2d}] W{tid} {kind:5s} фаза {ph}")
    problems = check(events)
    hung = [t.name for t in threads if t.is_alive()]
    for p in problems:
        print("НАРУШЕНИЕ:", p)
    print(f"зависших потоков: {len(hung)}")
    ok = not problems and not hung
    print("РЕЗУЛЬТАТ:", "OK" if ok else "FAIL")
    return ok


if __name__ == "__main__":
    sys.exit(0 if run(Barrier(N_THREADS), "барьер на условной переменной") else 1)
