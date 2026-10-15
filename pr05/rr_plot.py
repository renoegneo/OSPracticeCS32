import matplotlib
matplotlib.use("Agg")                   # рисуем в файл: окон в WSL нет
import matplotlib.pyplot as plt

from sched import load, simulate, metrics

QUANTA = range(1, 11)    # ручка: диапазон кванта
procs = load("set2.txt")

waits, resps, switches = [], [], []
for q in QUANTA:
    _, avg = metrics(procs, simulate(procs, "rr", quantum=q))
    waits.append(avg["waiting"])
    resps.append(avg["response"])
    switches.append(avg["switches"])
    print(f"q={q:2}  ожидание={avg['waiting']:.2f}  отклик={avg['response']:.2f}  "
          f"переключений={avg['switches']}")

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))
ax1.plot(QUANTA, waits, marker="o", label="среднее ожидание")
ax1.plot(QUANTA, resps, marker="s", label="среднее время отклика")
ax1.set_xlabel("квант")
ax1.set_ylabel("время")
ax1.legend()
ax1.grid(True)
ax2.plot(QUANTA, switches, marker="o", color="tab:red")
ax2.set_xlabel("квант")
ax2.set_ylabel("число переключений")
ax2.grid(True)
fig.suptitle("RR на set2")
fig.tight_layout()
fig.savefig("rr_plot.png", dpi=120)
