import os
import time

pid = os.fork()
if pid == 0:
    os._exit(0)                       # ребёнок сразу умирает
print(f"Родитель PID={os.getpid()}, ребёнок PID={pid} (станет зомби)", flush=True)
time.sleep(20)                        # родитель жив, но wait() не зовёт
