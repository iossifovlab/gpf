from django.core.cache import caches
import pickle
import hashlib


MAX_CHUNK_SIZE = 1024*1024

def hash_key(key):
    return hashlib.sha1(key).hexdigest()


def store(key, value, chunksize=950000):
    hkey = hash_key(key)
    memcache = caches['pre']
    serialized = pickle.dumps(value, 2)
    values = {}
    for i in xrange(0, len(serialized), chunksize):
        values['%s.%s' % (hkey, i//chunksize)] = serialized[i: i+chunksize]
    memcache.set_many(values)


def retrieve(key):
    hkey = hash_key(key)
    memcache = caches['pre']
    result = memcache.get_many(['%s.%s' % (hkey, i) for i in xrange(32)])
    l = [v for v in result.values() if v is not None]
    if len(l) == 0:
        return None
    serialized = ''.join(l)
    return pickle.loads(serialized)


