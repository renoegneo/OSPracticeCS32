"""ПР-6: НАМЕРЕННО сломанная версия — семафоры есть, мьютекса нет (гонка за head/tail/count)."""
import sys
import threading
import time
from pc_common import Ring, run_test

RACE_DELAY = 0.0001  # ручка: пауза между «прочитал tail» и «записал» — расширяет окно гонки
                     # (в CPython из-за GIL гонка иначе ловится редко; 0 = как есть, можно не поймать)


class NoMutexBuffer(Ring):
    def __init__(self):
        super().__init__()
        self.empty = threading.Semaphore(self.cap)
        self.full = threading.Semaphore(0)

    def put(self, item):
        self.empty.acquire()
        t = self.tail                 # два производителя могут прочитать ОДИН И ТОТ ЖЕ tail...
        time.sleep(RACE_DELAY)
        self.slots[t] = item          # ...и записать в один слот: один элемент затёрт
        self.tail = (t + 1) % self.cap
        self.count += 1               # += это три действия (прочитать, прибавить, записать), не атомарно
        self.full.release()

    def get(self):
        self.full.acquire()
        h = self.head
        time.sleep(RACE_DELAY)
        item = self.slots[h]          # два потребителя могут прочитать один слот: дубликат
        self.head = (h + 1) % self.cap
        self.count -= 1
        self.empty.release()
        return item


if __name__ == "__main__":
    sys.exit(0 if run_test(NoMutexBuffer(), "БЕЗ мьютекса (сломано)") else 1)
