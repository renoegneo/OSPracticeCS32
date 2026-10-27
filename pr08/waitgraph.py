import sys


def find_cycle(graph):
    """DFS по графу {поток: [потоки, которых он ждёт]}. Возвращает список участников цикла или None."""
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {}
    stack = []                                   # текущий путь

    def dfs(u):
        color[u] = GRAY
        stack.append(u)
        for v in graph.get(u, []):
            if color.get(v, WHITE) == GRAY:      # вернулись на путь: нашли цикл
                return stack[stack.index(v):]
            if color.get(v, WHITE) == WHITE:
                found = dfs(v)
                if found:
                    return found
        stack.pop()
        color[u] = BLACK
        return None

    for node in list(graph):
        if color.get(node, WHITE) == WHITE:
            cycle = dfs(node)
            if cycle:
                return cycle
    return None


def replay(path):
    owner, waiting = {}, {}                      # owner: ресурс -> поток, waiting: поток -> ресурс
    with open(path) as f:
        events = [l.split() for l in f if l.strip() and not l.startswith("#")]
    for n, (action, thread, res) in enumerate(events, 1):
        if action == "acquire":
            owner[res] = thread
            waiting.pop(thread, None)
        elif action == "release":
            owner.pop(res, None)
        elif action == "wait":
            waiting[thread] = res
        # граф ОЖИДАНИЯ: поток -> владелец ресурса, которого он ждёт
        graph = {t: [owner[r]] for t, r in waiting.items() if r in owner and owner[r] != t}
        cycle = find_cycle(graph)
        if cycle:
            print(f"Событие {n} ({action} {thread} {res}): ВЗАИМОБЛОКИРОВКА")
            for t, r in waiting.items():
                print(f"  {t} ждёт {r}, им владеет {owner.get(r)}")
            print("Участники цикла:", " -> ".join(cycle + [cycle[0]]))
            return
    print("Взаимоблокировки нет")


if __name__ == "__main__":
    replay(sys.argv[1])
