"""ПР-6, п.1(б): производитель–потребитель на мьютексе + условных переменных."""
import sys
import threading
from pc_common import Ring, run_test


class CondBuffer(Ring):
    def __init__(self):
        super().__init__()
        self.lock = threading.Lock()                    # ОДИН мьютекс на всё
        self.not_full = threading.Condition(self.lock)  # «в буфере есть место»
        self.not_empty = threading.Condition(self.lock) # «в буфере есть элемент»
        # Две условные переменные на одном замке: каждый будит только «своих» ждущих.
        # Это всё ещё один мьютекс + условные переменные (см. п.1(б) задания).

    def put(self, item):
        with self.not_full:                 # входим в with = берём self.lock
            while self.count == self.cap:   # while, не if: условие надо перепроверять после пробуждения
                self.not_full.wait()        # wait ОТПУСКАЕТ замок и спит, при пробуждении берёт замок обратно
            self._put_raw(item)
            self.not_empty.notify()         # разбудить одного потребителя

    def get(self):
        with self.not_empty:
            while self.count == 0:
                self.not_empty.wait()
            item = self._get_raw()
            self.not_full.notify()          # разбудить одного производителя
        return item


if __name__ == "__main__":
    sys.exit(0 if run_test(CondBuffer(), "(б) мьютекс + условные переменные") else 1)
