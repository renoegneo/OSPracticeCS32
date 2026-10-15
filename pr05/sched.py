import argparse
import copy
from collections import deque

ALGOS = ["fcfs", "sjf", "srtf", "priority", "rr"]


class Process:
    def __init__(self, pid, arrival, burst, priority):
        self.pid = pid
        self.arrival = arrival
        self.burst = burst
        self.priority = priority        # чем МЕНЬШЕ число, тем важнее процесс
        self.remaining = burst          # сколько ещё осталось отработать
        self.eff_priority = priority    # приоритет с учётом старения
        self.wait_ticks = 0             # сколько тактов процесс прождал в очереди


def load(path):
    """Читает файл: PID arrival burst priority (приоритет можно опустить)."""
    procs = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            priority = int(parts[3]) if len(parts) > 3 else 0
            procs.append(Process(parts[0], int(parts[1]), int(parts[2]), priority))
    return procs


def _add(intervals, pid, start, end):
    """Добавляет интервал; если он продолжает предыдущий того же процесса, склеивает."""
    if intervals and intervals[-1][0] == pid and intervals[-1][2] == start:
        intervals[-1] = (pid, intervals[-1][1], end)
    else:
        intervals.append((pid, start, end))


def _generic(procs, algorithm, aging):
    """FCFS, SJF, SRTF, Priority: симуляция по тактам (по 1 единице времени)."""
    keys = {                                  # по какому ключу выбираем следующий процесс
        "fcfs": lambda p: (p.arrival,),
        "sjf": lambda p: (p.burst, p.arrival),
        "srtf": lambda p: (p.remaining, p.arrival),
        "priority": lambda p: (p.eff_priority, p.arrival),
    }
    preemptive = algorithm in ("srtf", "priority")   # может ли выбор меняться каждый такт
    n, i, t, done = len(procs), 0, 0, 0
    ready, running, intervals = [], None, []
    while done < n:
        while i < n and procs[i].arrival <= t:        # прибывшие к моменту t
            ready.append(procs[i])
            i += 1
        if not ready:                                  # CPU простаивает до следующего прибытия
            _add(intervals, None, t, procs[i].arrival)
            t = procs[i].arrival
            continue
        if running is None or preemptive:
            running = min(ready, key=keys[algorithm])
        p = running
        p.remaining -= 1
        _add(intervals, p.pid, t, t + 1)
        t += 1
        if aging:                                      # старение: ждущим растёт приоритет
            for q in ready:
                if q is not p:
                    q.wait_ticks += 1
                    if q.wait_ticks % aging == 0 and q.eff_priority > 0:
                        q.eff_priority -= 1
        if p.remaining == 0:
            ready.remove(p)
            running = None
            done += 1
    return intervals


def _rr(procs, quantum):
    n, i, t = len(procs), 0, 0
    queue, intervals = deque(), []
    while i < n or queue:
        if not queue and procs[i].arrival > t:         # простой до следующего прибытия
            _add(intervals, None, t, procs[i].arrival)
            t = procs[i].arrival
        while i < n and procs[i].arrival <= t:
            queue.append(procs[i])
            i += 1
        p = queue.popleft()
        run = min(quantum, p.remaining)
        _add(intervals, p.pid, t, t + run)
        t += run
        p.remaining -= run
        while i < n and procs[i].arrival <= t:         # СНАЧАЛА прибывшие к концу кванта...
            queue.append(procs[i])
            i += 1
        if p.remaining > 0:                            # ...и только потом вытесненный
            queue.append(p)
    return intervals


def simulate(processes, algorithm, **params):
    """Возвращает список интервалов (pid, начало, конец); pid=None значит простой."""
    procs = sorted(copy.deepcopy(processes), key=lambda p: p.arrival)  # копия: оригинал не портим
    if algorithm == "rr":
        return _rr(procs, params.get("quantum", 3))
    return _generic(procs, algorithm, params.get("aging", 0))


def count_switches(intervals):
    """Число переключений: соседние интервалы разных процессов."""
    real = [iv for iv in intervals if iv[0] is not None]
    return sum(1 for a, b in zip(real, real[1:]) if a[0] != b[0])


def metrics(processes, intervals):
    first, last = {}, {}
    for pid, s, e in intervals:
        if pid is None:
            continue
        first.setdefault(pid, s)       # первый запуск
        last[pid] = e                  # последнее завершение
    rows = []
    for p in processes:
        turnaround = last[p.pid] - p.arrival                 # оборот = конец - прибытие
        rows.append({"pid": p.pid, "arrival": p.arrival, "burst": p.burst,
                     "finish": last[p.pid],
                     "waiting": turnaround - p.burst,         # ожидание = оборот - burst
                     "turnaround": turnaround,
                     "response": first[p.pid] - p.arrival})   # отклик = первый запуск - прибытие
    n = len(rows)
    avg = {k: sum(r[k] for r in rows) / n for k in ("waiting", "turnaround", "response")}
    total = intervals[-1][2]                                  # время от 0 до конца
    busy = sum(e - s for pid, s, e in intervals if pid is not None)
    avg["cpu"] = busy / total * 100
    avg["switches"] = count_switches(intervals)
    return rows, avg


def print_report(title, processes, intervals):
    rows, avg = metrics(processes, intervals)
    print(f"\n=== {title} ===")
    print("Гант: " + " ".join(f"[{s}-{e}]{pid or 'idle'}" for pid, s, e in intervals))
    print(f"{'PID':<5}{'прибыт.':>8}{'burst':>7}{'конец':>7}{'ожид.':>7}{'оборот':>8}{'отклик':>8}")
    for r in rows:
        print(f"{r['pid']:<5}{r['arrival']:>8}{r['burst']:>7}{r['finish']:>7}"
              f"{r['waiting']:>7}{r['turnaround']:>8}{r['response']:>8}")
    print(f"Среднее ожидание: {avg['waiting']:.2f} | средний оборот: {avg['turnaround']:.2f} | "
          f"средний отклик: {avg['response']:.2f} | загрузка CPU: {avg['cpu']:.1f}% | "
          f"переключений: {avg['switches']}")


def print_summary(processes, params):
    print(f"{'алгоритм':<12}{'ожидание':>10}{'оборот':>10}{'отклик':>10}{'CPU,%':>8}{'перекл.':>9}")
    for algo in ALGOS:
        _, avg = metrics(processes, simulate(processes, algo, **params))
        name = f"rr(q={params['quantum']})" if algo == "rr" else algo
        print(f"{name:<12}{avg['waiting']:>10.2f}{avg['turnaround']:>10.2f}"
              f"{avg['response']:>10.2f}{avg['cpu']:>8.1f}{avg['switches']:>9}")


def main():
    ap = argparse.ArgumentParser(description="Симулятор планирования CPU")
    ap.add_argument("file")
    ap.add_argument("--algo", default="fcfs", choices=ALGOS + ["all"])
    ap.add_argument("--quantum", type=int, default=3, help="квант для RR")
    ap.add_argument("--aging", type=int, default=0,
                    help="priority: каждые N тактов ожидания приоритет растёт (0 = выкл.)")
    args = ap.parse_args()
    procs = load(args.file)
    params = {"quantum": args.quantum, "aging": args.aging}
    if args.algo == "all":
        print_summary(procs, params)
    else:
        print_report(args.algo, procs, simulate(procs, args.algo, **params))


if __name__ == "__main__":
    main()
