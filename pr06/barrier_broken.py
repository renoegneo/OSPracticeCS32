"""ПР-6: НАМЕРЕННО сломанный «барьер» — wait() ничего не ждёт."""
import sys
from barrier import run, N_THREADS


class NoBarrier:
    def wait(self):
        pass   # потоки не ждут друг друга


if __name__ == "__main__":
    sys.exit(0 if run(NoBarrier(), "БЕЗ барьера (сломано)") else 1)
