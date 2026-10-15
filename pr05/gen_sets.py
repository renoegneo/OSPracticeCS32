import random

random.seed(5)    # ручка: seed, чтобы наборы воспроизводились

def write(name, rows):
    with open(name, "w") as f:
        f.write("# PID arrival burst priority\n")
        for r in rows:
            f.write(" ".join(map(str, r)) + "\n")

# set1: контрольный (приоритеты в условии не заданы, выбраны произвольно;
# на FCFS/SJF/SRTF/RR они не влияют)
write("set1.txt", [("P1", 0, 8, 3), ("P2", 1, 4, 1), ("P3", 2, 9, 4), ("P4", 3, 5, 2)])

# set2: 20 CPU-bound процессов (длинные бёрсты 20..40)
write("set2.txt", [(f"P{i}", random.randint(0, 20), random.randint(20, 40),
                    random.randint(1, 5)) for i in range(1, 21)])

# set3: 19 коротких (1..6) и один длинный (100)
rows = [("P1", 0, 100, 3)]
rows += [(f"P{i}", random.randint(1, 40), random.randint(1, 6),
          random.randint(1, 5)) for i in range(2, 21)]
write("set3.txt", rows)

# set4: набор для голодания. P1 (приоритет 5) и поток из 12 важных
# процессов H1..H12 (приоритет 1), каждый приходит ровно когда кончился предыдущий
rows = [("P1", 0, 5, 5)]
rows += [(f"H{k}", 4 * (k - 1), 4, 1) for k in range(1, 13)]
write("set4_starve.txt", rows)
