import statistics
import time
import urllib.request
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor

URLS = [f"http://127.0.0.1:8000/file{i}" for i in range(20)]   # 20 URL
N_WORKERS = 4    # ручка: число потоков / процессов
REPEATS = 3      # ручка: число повторов

def fetch(url):
    with urllib.request.urlopen(url) as r:
        return len(r.read())

def run_sequential():
    return sum(fetch(u) for u in URLS)

def run_threads():
    with ThreadPoolExecutor(max_workers=N_WORKERS) as ex:
        return sum(ex.map(fetch, URLS))

def run_processes():
    with ProcessPoolExecutor(max_workers=N_WORKERS) as ex:
        return sum(ex.map(fetch, URLS))

def bench(name, func):
    times = []
    for _ in range(REPEATS):
        t0 = time.perf_counter()
        func()
        times.append(time.perf_counter() - t0)
    print(f"{name:14} времена={[round(t, 2) for t in times]} "
          f"медиана={statistics.median(times):.2f} c", flush=True)

if __name__ == "__main__":
    bench("последовательно", run_sequential)
    bench("потоки", run_threads)
    bench("процессы", run_processes)
