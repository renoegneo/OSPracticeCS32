import faulthandler
import threading
import time

faulthandler.dump_traceback_later(5, exit=True)

lock_a = threading.Lock()
lock_b = threading.Lock()

def worker1():
	with lock_a:
		print("T1 взял А, жду В")
		time.sleep(0.2)
		with lock_b:
			print("T1 взял А и В")

def worker2():
	with lock_b:
		print("T2 взял В, жду А")
		time.sleep(0.2)
		with lock_a:
			print("T2 взял В и А")

t1 = threading.Thread(target=worker1)
t2 = threading.Thread(target=worker2)
t1.start(); t2.start()
t1.join(); t2.join()
faulthandler.cancel_dump_traceback_later()
print("готово")
