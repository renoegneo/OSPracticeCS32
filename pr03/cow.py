import os

def mem(label):
    rss = pss = 0
    with open("/proc/self/smaps_rollup") as f:
        for line in f:
            if line.startswith("Rss:"):
                rss = int(line.split()[1])
            elif line.startswith("Pss:"):
                pss = int(line.split()[1])
    print(f"{label}: RSS={rss // 1024} МБ, Pss={pss // 1024} МБ", flush=True)

SIZE = 3_000_000                      # ручка: размер списка (больше -> нагляднее)
big = list(range(SIZE))               # большой список в родителе
mem("Родитель до fork")

pid = os.fork()
if pid == 0:
    mem("Ребёнок сразу после fork")   # список ещё не трогали
    for i in range(len(big)):
        big[i] += 1                   # запись -> ядро копирует страницы
    mem("Ребёнок после изменения")
    os._exit(0)
os.wait()
