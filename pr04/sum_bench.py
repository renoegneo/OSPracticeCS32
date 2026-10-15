import multiprocessing as mp
import statistics
import threading
import time

N_WORKERS = 4    # ручка: число потоков / процессов
REPEATS = 3      # ручка: число повторов (медиана берётся по ним)

# Загрузка данных НЕ входит в замер
with open("numbers.txt") as f:
    nums = [int(line) for line in f]
EXPECTED = sum(nums)    # эталон для проверки правильности

def partial_sum(a, b):
    """Сумма кусочка nums[a:b] обычным циклом (код Python под GIL)."""
    total = 0
    for x in nums[a:b]:
        total += x
    return total

def chunks():
    """Делит список на N_WORKERS кусков; хвост достаётся последнему."""
    step = len(nums) // N_WORKERS
    bounds = [(i * step, (i + 1) * step) for i in range(N_WORKERS)]
    bounds[-1] = (bounds[-1][0], len(nums))
    return bounds

def run_single():
    return partial_sum(0, len(nums))

def run_threads():
    results = [0] * N_WORKERS
    def work(i, a, b):
        results[i] = partial_sum(a, b)
    threads = [threading.Thread(target=work, args=(i, a, b))
               for i, (a, b) in enumerate(chunks())]
    for t in threads:       # сначала запускаем ВСЕХ...
        t.start()
    for t in threads:       # ...и только потом ждём (иначе потоки пойдут по очереди)
        t.join()
    return sum(results)

def run_processes():
    # создание пула входит в замер: это реальная цена процессов
    with mp.Pool(N_WORKERS) as pool:
        return sum(pool.starmap(partial_sum, chunks()))

def bench(name, func):
    times = []
    for _ in range(REPEATS):
        t0 = time.perf_counter()
        result = func()
        times.append(time.perf_counter() - t0)
        assert result == EXPECTED, "сумма не сошлась!"
    print(f"{name:10} времена={[round(t, 2) for t in times]} "
          f"медиана={statistics.median(times):.2f} c", flush=True)

if __name__ == "__main__":
    mp.set_start_method("fork")    # на Linux это и так по умолчанию, фиксируем явно
    bench("1 поток", run_single)
    bench("4 потока", run_threads)
    bench("4 процесса", run_processes)
