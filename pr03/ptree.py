import os

def read_status(pid):
    """Читает /proc/<pid>/status в словарь {поле: значение}."""
    info = {}
    with open(f"/proc/{pid}/status") as f:
        for line in f:
            key, _, value = line.partition(":")
            info[key] = value.strip()
    return info

my_uid = str(os.getuid())
procs = {}

for entry in os.listdir("/proc"):
    if not entry.isdigit():          # нас интересуют только папки-числа (PID)
        continue
    try:
        st = read_status(entry)
    except (FileNotFoundError, ProcessLookupError, PermissionError):
        continue                      # процесс умер, пока мы читали, это нормально
    if st["Uid"].split()[0] != my_uid:
        continue                      # чужой процесс (root и т.д.)
    procs[int(entry)] = {
        "name": st["Name"],
        "state": st["State"].split()[0],
        "ppid": int(st["PPid"]),
        "rss": st.get("VmRSS", "0 kB").split()[0],  # у зомби VmRSS нет
    }

children = {}
for pid, p in procs.items():
    children.setdefault(p["ppid"], []).append(pid)

def show(pid, depth=0):
    p = procs[pid]
    print(f'{"  " * depth}{pid} {p["name"]} [{p["state"]}] RSS={p["rss"]} kB')
    for child in sorted(children.get(pid, [])):
        show(child, depth + 1)       # рекурсия: печатаем детей с отступом больше

# корни дерева: те, чей родитель не наш (например, родитель root)
for root in sorted(pid for pid, p in procs.items() if p["ppid"] not in procs):
    show(root)
