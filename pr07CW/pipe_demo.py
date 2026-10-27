import os

r, w = os.pipe()
pid = os.fork()

if pid == 0:
	os.close(r)
	msg = f"Привет от ребенка, PID={os.getpid()}\n"
	os.write(w, msg.encode())
	os.close(w)
	os._exit(0)

else:
	os.close(w)
	data = os.read(r, 1024)
	os.close(r)
	os.waitpid(pid, 0)
	print("Родитель получил:", data.decode().strip())
