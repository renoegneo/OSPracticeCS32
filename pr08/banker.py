import sys


def load(path):
    """Читает файл: строка available + по строке на процесс (PID, Allocation, Max)."""
    avail, alloc, maxm = None, {}, {}
    with open(path) as f:
        for line in f:
            line = line.split("#")[0].strip()          # отрезаем комментарии
            if not line:
                continue
            parts = line.split()
            if parts[0] == "available":
                avail = [int(x) for x in parts[1:]]
            else:
                m = len(avail)                          # число типов ресурсов
                nums = [int(x) for x in parts[1:]]
                alloc[parts[0]] = nums[:m]
                maxm[parts[0]] = nums[m:]
    return avail, alloc, maxm


def le(a, b):
    """a <= b покомпонентно."""
    return all(x <= y for x, y in zip(a, b))


def need_of(alloc, maxm):
    return {p: [m - a for m, a in zip(maxm[p], alloc[p])] for p in alloc}


def is_safe(avail, alloc, maxm):
    """Алгоритм безопасности. Возвращает (безопасно?, порядок завершения)."""
    need = need_of(alloc, maxm)
    work = avail[:]                                     # копия: настоящий Available не трогаем
    finish = {p: False for p in alloc}
    order = []
    progress = True
    while progress:
        progress = False
        for p in alloc:
            if not finish[p] and le(need[p], work):
                work = [w + a for w, a in zip(work, alloc[p])]   # процесс завершился и вернул ресурсы
                finish[p] = True
                order.append(p)
                progress = True
    return all(finish.values()), order


def request(avail, alloc, maxm, pid, req):
    """Обработка запроса. Меняет состояние только если запрос одобрен."""
    if pid not in alloc or len(req) != len(avail):
        return "ERROR (неизвестный процесс или неверная длина вектора)"
    need = need_of(alloc, maxm)
    if not le(req, need[pid]):
        return "ERROR (запрос превышает заявленный максимум: Request > Need)"
    if not le(req, avail):
        return "WAIT (ресурсов сейчас нет: Request > Available)"
    for j, r in enumerate(req):                         # пробное выделение
        avail[j] -= r
        alloc[pid][j] += r
    safe, order = is_safe(avail, alloc, maxm)
    if not safe:
        for j, r in enumerate(req):                     # ОТКАТ: возвращаем как было
            avail[j] += r
            alloc[pid][j] -= r
        return "DENIED (состояние стало бы небезопасным, выполнен откат)"
    return "GRANTED (безопасная последовательность: " + " -> ".join(order) + ")"


def main():
    avail, alloc, maxm = load(sys.argv[1])
    need = need_of(alloc, maxm)
    print("Available:", avail)
    for p in alloc:
        print(f"{p}: Allocation={alloc[p]} Max={maxm[p]} Need={need[p]}")
    safe, order = is_safe(avail, alloc, maxm)
    print("Начальное состояние:", "SAFE  " + " -> ".join(order) if safe else "UNSAFE")
    for line in sys.stdin:                              # запросы: "P1 1 0 2"
        parts = line.split()
        if not parts:
            continue
        pid, req = parts[0], [int(x) for x in parts[1:]]
        print(f"request {pid} {req}: {request(avail, alloc, maxm, pid, req)}")


if __name__ == "__main__":
    main()
