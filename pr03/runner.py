import os
import sys
import time

# использование: python3 runner.py N команда [аргументы...]
n = int(sys.argv[1])
cmd = sys.argv[2:]

started = {}                          # PID ребёнка -> время старта

for _ in range(n):
    pid = os.fork()
    if pid == 0:                      # --- ветка ребёнка ---
        try:
            os.execvp(cmd[0], cmd)    # ищет команду в PATH, заменяет процесс
        except OSError:
            os._exit(127)             # exec не удался (нет такой команды)
    started[pid] = time.time()        # --- ветка родителя ---

for _ in range(n):
    pid, status = os.wait()           # ждём любого ребёнка
    elapsed = time.time() - started[pid]
    code = os.waitstatus_to_exitcode(status)
    print(f"PID={pid} код={code} время={elapsed:.2f} c")
