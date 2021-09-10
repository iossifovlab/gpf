import time

# from dae.backends.impala.impala_helpers import ImpalaHelpers
from dae.backends.impala.impala_query_executor import ImpalaQueryExecutor


class FakeCursor:

    def __init__(self, delay):
        self._closed = False
        self._operation = None
        self.delay = delay

    def close(self):
        self._closed = True

    def execute(self, query):
        self._operation = query
        time.sleep(self.delay)

    def fetchone(self):
        if self._closed:
            raise AttributeError()

        return (1, 2, 3)

    def __next__(self):
        return self.fetchone()

    def __iter__(self):
        return self


class FakeConnection:

    def __init__(self, delay):
        self._closed = False
        self.delay = delay

    def cursor(self):
        return FakeCursor(self.delay)


class FakeImpalaHelpers:
    def __init__(self, delay=0.0):
        self.delay = delay

    def connection(self):
        return FakeConnection(self.delay)

# def test_impala_query_runner():
#     connection = dbapi.connect(host="localhost")
#     query = "SELECT " \
#         "COUNT(DISTINCT bucket_index, summary_index, family_index) " \
#         "FROM data_hg19_local.sfari_spark_wes_p_variants "

#     runner = ImpalaQueryRunner(connection, query)
#     for row in runner:
#         print(row)


def test_impala_query_executor_close_before_start():
    impala_helpers = FakeImpalaHelpers(10)
    executor = ImpalaQueryExecutor(impala_helpers)
    query = "SELECT " \
        "DISTINCT bucket_index, summary_index, family_index " \
        "FROM data_hg19_local.sfari_spark_wes_p_variants "

    runner = executor.submit(query)
    time.sleep(0.5)
    runner.close()

    for row in runner:
        if row is None:
            continue
        print("get row...")
        print(row)
        break

    time.sleep(2.0)
    runner.close()


def test_impala_query_executor_close_when_full():
    impala_helpers = FakeImpalaHelpers()
    executor = ImpalaQueryExecutor(impala_helpers)
    query = "SELECT " \
        "DISTINCT bucket_index, summary_index, family_index " \
        "FROM data_hg19_local.sfari_spark_wes_p_variants "

    runner = executor.submit(query)
    # time.sleep(2.0)
    # runner.close()

    for row in runner:
        if row is None:
            continue
        print("get row...")
        print(row)
        break

    time.sleep(2.0)
    runner.close()


# def test_impala_connection():
#     connection = dbapi.connect(host="localhost")

#     cursor = connection.cursor()

#     def runner():
#         try:
#             print("RUNNER STARTED...")
#             start = time.time()
#             cursor.execute(
#                 "SELECT "
#                 "COUNT(DISTINCT bucket_index, summary_index, family_index) "
#                 "FROM data_hg19_local.sfari_spark_wes_p_variants "
#             )
#             elapsed = time.time() - start
#             print(f"cursor execute finished in {elapsed:0.3f} secs")

#             start = time.time()
#             for row in cursor:
#                 print(row)
#                 elapsed = time.time() - start
#                 print(f"first row fetched in {elapsed:0.3f} secs")
#                 break
#         except Exception as ex:
#             print("exception in runner:", type(ex))
#             traceback.print_tb(ex.__traceback__)

#     executor = ThreadPoolExecutor(max_workers=6)
#     fut = executor.submit(runner)

#     print(
#         "fut status: running=", fut.running(),
#         "done=", fut.done())
#     time.sleep(2)

#     print("going to close cursor...")
#     cursor.close()

#     # print("going to cancel the future:")
#     # print("cancel:", fut.cancel())

#     print("going to wait for future to finish...")
#     wait([fut])

#     print(
#         "fut status: running=", fut.running(), "done=", fut.done(), 
#         "exception=", fut.exception())
#     cursor.close()

#     print("CURSOR CLOSED")


# def test_future():
#     fut = Future()
#     assert fut is not None


# class IteratorCheck:

#     def __init__(self, count):
#         self.count = count
#         self.data = list(range(count))

#     def __iter__(self):
#         return self

#     def __next__(self):
#         if self.count <= 0:
#             raise StopIteration()

#         self.count -= 1
#         return self.data[self.count]

#     def close(self):
#         self.count = -1


# def test_close_iterator():
#     it = IteratorCheck(10)

#     for d in it:
#         print(d)
#         it.close()
