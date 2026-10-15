import multiprocessing as mp
import threading

data = []    # глобальный список

def add(tag):
    data.append(tag)
    print(f"  внутри ({tag}): {data}", flush=True)

if __name__ == "__main__":
    t = threading.Thread(target=add, args=("поток",))
    t.start()
    t.join()
    print("Родитель после потока:", data)

    p = mp.Process(target=add, args=("процесс",))
    p.start()
    p.join()
    print("Родитель после процесса:", data)
