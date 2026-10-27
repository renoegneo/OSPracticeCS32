import os
import signal
import time

def handler(signum, frame):
	name = signal.Signals(signum).name
	print(f"Получет {name}, но я не завершаюсь")


signal.signal(signal.SIGINT, handler)
print("Мой PID:", os.getpid())

while True:
	time.sleep(1)
