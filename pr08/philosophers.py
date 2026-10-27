import random
import sys
import threading
import time

N = 5               # ручка: число философов
THINK = 0.01        # ручка: макс. время размышления, с
PAUSE = 0.02        # ручка: пауза между первой и второй вилкой
EAT = 0.05          # ручка: время еды, с
DURATION = 5        # ручка: длительность опыта, с


def philosopher(i, mode, forks, seats, stats, stop):
    left, right = i, (i + 1) % N
    first, second = left, right
    if mode == "ordered":
        first, second = min(left, right), max(left, right)    # нумерация: сначала меньший номер
    while not stop.is_set():
        time.sleep(random.uniform(0, THINK))                  # думает
        if mode == "limited":
            seats.acquire()                                   # место за столом (их N-1)
        forks[first].acquire()
        time.sleep(PAUSE)
        forks[second].acquire()
        stats[i] += 1                                         # поел
        time.sleep(EAT)
        forks[second].release()
        forks[first].release()
        if mode == "limited":
            seats.release()


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in ("naive", "ordered", "limited"):
        sys.exit("использование: python3 philosophers.py naive|ordered|limited")
    mode = sys.argv[1]
    forks = [threading.Lock() for _ in range(N)]
    seats = threading.Semaphore(N - 1)
    stats = [0] * N
    stop = threading.Event()
    threads = [threading.Thread(target=philosopher, args=(i, mode, forks, seats, stats, stop),
                                daemon=True)     # daemon: застрявшие потоки не мешают выходу
               for i in range(N)]
    for t in threads:
        t.start()
    time.sleep(DURATION)
    stop.set()
    for t in threads:
        t.join(timeout=0.5)
    stuck = [i for i, t in enumerate(threads) if t.is_alive()]
    print(f"режим={mode}: за {DURATION} с поели {stats}, всего {sum(stats)}")
    print("ЗАВИСЛИ философы:", stuck if stuck else "нет")


if __name__ == "__main__":
    main()

