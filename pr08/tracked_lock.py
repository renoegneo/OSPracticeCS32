import threading

from waitgraph import find_cycle


class DeadlockError(Exception):
    """Бросается вместо зависания, когда запрос замка замкнул цикл ожидания."""


_guard = threading.Lock()      # защищает таблицы ниже
_owner = {}                    # TrackedLock -> имя потока-владельца
_waiting = {}                  # имя потока -> TrackedLock, которого он ждёт


def _graph():
    """Граф ожидания: поток -> [владелец замка, которого он ждёт]."""
    return {t: [_owner[l]] for t, l in _waiting.items() if l in _owner and _owner[l] != t}


class TrackedLock:
    def __init__(self, name):
        self.name = name
        self._lock = threading.Lock()

    def acquire(self):
        me = threading.current_thread().name
        with _guard:
            _waiting[me] = self                   # записываем: «я жду этот замок»
            cycle = find_cycle(_graph())
            if cycle:
                del _waiting[me]
                raise DeadlockError(f"{me} запросил замок {self.name}; цикл ожидания: "
                                    + " -> ".join(cycle + [cycle[0]]))
        self._lock.acquire()                      # здесь можно честно заблокироваться: цикла нет
        with _guard:
            del _waiting[me]
            _owner[self] = me

    def release(self):
        with _guard:
            del _owner[self]                      # сначала снимаем владельца, потом отпускаем
        self._lock.release()

    def __enter__(self):
        self.acquire()
        return self

    def __exit__(self, *exc):
        self.release()
