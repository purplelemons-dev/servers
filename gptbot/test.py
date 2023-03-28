
from time import sleep, perf_counter
from threading import Thread

class shared:
    def __init__(self):
        self.running = True
        self.history = []
    def off(self):
        self.running = False
    def display(self):
        print(self.history)

def thread1task(resource:shared):
    while resource.running:
        sleep(1)
    print("t1 done")

res = shared()
t1 = Thread(target=thread1task, args=(res,))
t1.start()
while True:
    try:
        usin = input(">>> ")
        if usin == "exit":
            raise KeyboardInterrupt
        else:
            res.history.append(usin)
    except KeyboardInterrupt:
        res.off()
        res.display()
        t1.join()
        break
