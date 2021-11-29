import threading


def create_thread(func, args):
    t1 = threading.Thread(target=func, args=args)

    t1.start()
