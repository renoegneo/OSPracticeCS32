import random

COUNT = 10_000_000   # ручка: сколько чисел
random.seed(42)      # фиксируем seed, чтобы файл воспроизводился

with open("numbers.txt", "w") as f:
    for _ in range(COUNT // 100_000):         # пишем кусками, не всё в память сразу
        chunk = [str(random.randint(1, 100)) for _ in range(100_000)]
        f.write("\n".join(chunk) + "\n")
