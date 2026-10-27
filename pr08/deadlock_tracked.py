import faulthandler
import threading
import time

from tracked_lock import DeadlockError, TrackedLock

faulthandler.dump_traceback_later(5, exit=True)   # страховка: если детектор не сработал, будет дамп

lock_a = TrackedLock("A")
lock_b = TrackedLock("B")


def worker1():
    try:
        with lock_a:
            print("T1 взял A, жду B")
            time.sleep(0.2)
            with lock_b:
                print("T1 взял A и B")
    except DeadlockError as e:
        print("T1:", e)


def worker2():
    try:
        with lock_b:
            print("T2 взял B, жду A")
            time.sleep(0.2)
            with lock_a:
                print("T2 взял B и A")
    except DeadlockError as e:
        print("T2:", e)


t1 = threading.Thread(target=worker1, name="T1")
t2 = threading.Thread(target=worker2, name="T2")
t1.start(); t2.start()
t1.join(); t2.join()
faulthandler.cancel_dump_traceback_later()
print("готово")
