import VariantAnnotation
import coverage
import pytest
import csv
import gzip
import pickle
from DAE import genomesDB
import multiprocessing as mp
import time
import os
import Queue
import sys

QUEUE_END_MESSAGE = "That's all folks!"
MAX_FLUSH_TIME = 10.0

GA = genomesDB.get_genome()
gmDB = genomesDB.get_gene_models()


def search_for_effects(input_queue, output_queue,
                       all_tests_missing_lines):
    while (True):
        message = input_queue.get()
        if message == QUEUE_END_MESSAGE:
            return

        cov = coverage.Coverage()
        cov.start()
        loc = message["loc"]
        var = message["var"]
        VariantAnnotation.annotate_variant(gmDB, GA, loc=loc, var=var)
        cov.stop()
        current_variant_missing = set(cov.analysis2(VariantAnnotation)[3])
        diff_set = all_tests_missing_lines - current_variant_missing
        if len(diff_set) > 0:
            effect = {
                'lines': diff_set,
                'count': len(diff_set),
                'var': var,
                'loc': loc
            }
            output_queue.put(effect)
        if message["num"] % 10000 == 0:
            print("Line {} ok".format(message["num"]))


def get_all_tests_missing_lines():
    cov = coverage.Coverage()
    cov.start()
    pytest.main(['../tests/VariantAnnotation_tests.py'])
    cov.stop()
    return set(cov.analysis2(VariantAnnotation)[3])


def read_queue(q):
    start_time = time.time()
    with open("output", "wb") as f:
        while (True):
            try:
                message = q.get(timeout=MAX_FLUSH_TIME)
                if message == QUEUE_END_MESSAGE:
                    print(message)
                    return
                else:
                    pickle.dump(message, f, pickle.HIGHEST_PROTOCOL)
            except Queue.Empty:
                pass

            current_time = time.time()
            if current_time - start_time > MAX_FLUSH_TIME:
                f.flush()
                os.fsync(f.fileno())
                start_time = current_time


if __name__ == "__main__":
    path = sys.argv[1]
    limit = 0
    if len(sys.argv) > 2:
        limit = int(sys.argv[2])

    all_tests_missing_lines = get_all_tests_missing_lines()
    output_queue = mp.Queue()
    input_queue = mp.Queue()

    p = mp.Process(target=read_queue, args=(output_queue,))
    p.start()

    pool = mp.Pool(None, search_for_effects, [input_queue,
                                              output_queue,
                                              all_tests_missing_lines])
    try:
        with gzip.open(path) as f:
            reader = csv.DictReader(f, delimiter='\t')
            for i, line in enumerate(reader):
                if limit > 0 and i >= limit:
                    break
                message = {
                    "num": i,
                    "loc": line["chr"] + ":" + line["position"],
                    "var": line["variant"]
                }
                input_queue.put(message)

    finally:
        for i in range(0, mp.cpu_count()):
            input_queue.put(QUEUE_END_MESSAGE)
        pool.close()
        pool.join()
        output_queue.put(QUEUE_END_MESSAGE)
        p.join()
