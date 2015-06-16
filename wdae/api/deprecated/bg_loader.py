import threading
from DAE import get_gene_sets_symNS

_background = {}
_lock = threading.Lock()
_builder_started = False


class BackgroundBuilderTask (threading.Thread):

    def __init__(self, builders):
        threading.Thread.__init__(self)
        self.builders = builders

    def run(self):
        global _lock, _background,  _builder_started

        if not _lock.acquire(False):
            print("Background builder already started...")
            return
        else:
#             if _builder_started:
#                 _lock.release()
#                 return
            _builder_started = True

            try:
                print 'Starting background task'
                global _background
                for (func, args, key) in self.builders:
                    print("key: %s; args: %s" % (key,args))
                    res = func(*args)
                    _background[key] = res

            finally:
                print 'Exiting background task'
                _lock.release()


def get_background(key):
    global _lock, _background, _builder_started
    _lock.acquire(True)

    try:
        value = _background.get(key)
    finally:
        _lock.release()

    return value


def preload_background(builders):
    thread = BackgroundBuilderTask(builders)
    thread.start()


def gene_set_bgloader(gene_set_label):
    if 'denovo' == gene_set_label:
        return None
    else:
        gene_term = get_gene_sets_symNS(gene_set_label)
 
    return gene_term
