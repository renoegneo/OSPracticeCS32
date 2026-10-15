"""ПР-6, п.4: if вместо while вокруг wait. Запуск: python3 wakeup.py [if|while]"""
import sys
import threading
import time

MODE = sys.argv[1] if len(sys.argv) > 1 else "if"   # ручка: "if" (сломано) или "while" (правильно)
if MODE not in ("if", "while"):
    sys.exit("Использование: python3 wakeup.py [if|while]")

items = []
cond = threading.Condition()


def consumer(name):
    with cond:
        if MODE == "if":
            if not items:            # проверили условие ОДИН раз
                cond.wait()          # после пробуждения условие НЕ перепроверяется
        else:
            while not items:         # перепроверка после каждого пробуждения
                cond.wait()
        print(f"{name}: проснулся, items={items}", flush=True)
        if not items:
            print(f"{name}: НАРУШЕНИЕ — данных нет, а я иду их забирать", flush=True)
            return
        print(f"{name}: взял {items.pop()}", flush=True)


c1 = threading.Thread(target=consumer, args=("C1",), daemon=True)
c2 = threading.Thread(target=consumer, args=("C2",), daemon=True)
c1.start()
c2.start()
time.sleep(0.3)   # ручка: даём обоим время уснуть в wait()

with cond:
    items.append(1)
    print("P: положил 1, notify_all()", flush=True)
    cond.notify_all()          # проснутся ОБА, а элемент один

time.sleep(0.3)
with cond:
    items.append(2)            # второй элемент нужен, чтобы в режиме while дожил второй потребитель
    print("P: положил 2, notify_all()", flush=True)
    cond.notify_all()

c1.join(2)
c2.join(2)
print(f"осталось в items: {items}; зависших потоков: {sum(t.is_alive() for t in (c1, c2))}")
