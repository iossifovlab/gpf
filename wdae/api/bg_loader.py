import threading

background = {}
lock = threading.Lock()


class BackgroundBuilderTask (threading.Thread):

    def __init__(self, builders):
        threading.Thread.__init__(self)
        self.builders = builders

    def run(self):
        global lock
        if not lock.acquire(False):
            print("Background builder already started...")
            return
        else:
            try:
                print 'Starting background task'
                global background
                for (func, args, key) in self.builders:
                    res = func(*args)
                    background[key] = res
            finally:
                print 'Exiting background task'
                lock.release()


def get_background(key):
    global lock, background
    lock.acquire(True)
    value = background[key]
    lock.release()
    return value


def preload_background(builders):
    thread = BackgroundBuilderTask(builders)
    thread.start()
