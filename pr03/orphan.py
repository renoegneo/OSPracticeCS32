import os
import time

pid = os.fork()
if pid == 0:
    time.sleep(15)                    # ребёнок живёт дольше родителя
    print(f"\nРебёнок: мой новый PPID={os.getppid()}", flush=True)
    os._exit(0)
print(f"Родитель PID={os.getpid()}, ребёнок PID={pid}, родитель умирает", flush=True)
os._exit(0)
