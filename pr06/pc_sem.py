"""ПР-6, п.1(а): производитель–потребитель на 2 семафорах + мьютексе."""
import sys
import threading
from pc_common import Ring, run_test


class SemBuffer(Ring):
    def __init__(self):
        super().__init__()
        self.empty = threading.Semaphore(self.cap)  # сколько СВОБОДНЫХ слотов (старт: все 5)
        self.full = threading.Semaphore(0)          # сколько ЗАНЯТЫХ слотов (старт: 0)
        self.mutex = threading.Lock()               # защищает head/tail/count

    def put(self, item):
        self.empty.acquire()        # 1) ждём свободный слот (при полном буфере производитель спит тут)
        with self.mutex:            # 2) только потом мьютекс; with = гарантированный release
            self._put_raw(item)
        self.full.release()         # 3) будим потребителя: появился занятый слот

    def get(self):
        self.full.acquire()         # ждём, пока что-то лежит
        with self.mutex:
            item = self._get_raw()
        self.empty.release()        # освободился слот
        return item
    # ПОЧЕМУ сначала семафор, потом мьютекс: если наоборот, производитель возьмёт мьютекс
    # и уснёт на empty, а потребитель не сможет войти за мьютексом, чтобы освободить место
    # → взаимная блокировка (deadlock).


if __name__ == "__main__":
    sys.exit(0 if run_test(SemBuffer(), "(а) 2 семафора + мьютекс") else 1)
