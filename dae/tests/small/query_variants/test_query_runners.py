# pylint: disable=W0621,C0114,C0116,W0212,W0613
import queue
import time
from collections.abc import Generator
from concurrent.futures import ThreadPoolExecutor
from typing import Any

import pytest
from dae.query_variants.query_runners import QueryResult, QueryRunner


class MockQueryRunner(QueryRunner):
    """Mock query runner for testing."""

    def __init__(
        self,
        data: list[Any],
        delay: float = 0.0,
        **kwargs: Any,
    ):
        super().__init__(**kwargs)
        self.data = data
        self.delay = delay

    def run(self) -> None:
        """Execute the mock query."""
        try:
            for item in self.data:
                if self.is_closed():
                    break
                if self.delay > 0:
                    time.sleep(self.delay)
                # Apply deserializer
                value = self.deserializer(item)
                self.put_value_in_result_queue(value)
        except Exception as ex:  # noqa: BLE001
            self.put_value_in_result_queue(ex)
        finally:
            with self._status_lock:
                self._done = True


@pytest.fixture
def executor() -> Generator[ThreadPoolExecutor, None, None]:
    """Create a thread pool executor for testing."""
    pool = ThreadPoolExecutor(max_workers=4)
    yield pool
    pool.shutdown(wait=True)


def test_query_runner_basic_lifecycle(
    executor: ThreadPoolExecutor,
) -> None:
    """Test basic QueryRunner lifecycle."""
    runner = MockQueryRunner(data=[1, 2, 3])
    runner.set_study_id("test_study")

    assert not runner.is_started()
    assert not runner.is_done()
    assert not runner.is_closed()

    result_queue: queue.Queue = queue.Queue()
    runner.set_result_queue(result_queue)

    runner.start(executor)
    assert runner.is_started()

    time.sleep(0.1)  # Give runner time to complete
    assert runner.is_done()

    runner.close()
    assert runner.is_closed()


def test_query_runner_deserializer(
    executor: ThreadPoolExecutor,
) -> None:
    """Test QueryRunner with custom deserializer."""
    runner = MockQueryRunner(
        data=[1, 2, 3],
        deserializer=lambda x: x * 2,
    )
    runner.set_study_id("test_study")

    result_queue: queue.Queue = queue.Queue()
    runner.set_result_queue(result_queue)

    runner.start(executor)
    time.sleep(0.1)

    results = []
    while not result_queue.empty():
        results.append(result_queue.get())

    assert results == [2, 4, 6]


def test_query_runner_adapter(
    executor: ThreadPoolExecutor,
) -> None:
    """Test QueryRunner adapt method."""
    runner = MockQueryRunner(
        data=[1, 2, 3],
        deserializer=lambda x: x * 2,
    )
    runner.set_study_id("test_study")
    runner.adapt(lambda x: x + 1)

    result_queue: queue.Queue = queue.Queue()
    runner.set_result_queue(result_queue)

    runner.start(executor)
    time.sleep(0.1)

    results = []
    while not result_queue.empty():
        results.append(result_queue.get())

    assert results == [3, 5, 7]  # (x * 2) + 1


def test_query_runner_early_close(
    executor: ThreadPoolExecutor,
) -> None:
    """Test closing QueryRunner before completion."""
    runner = MockQueryRunner(
        data=list(range(100)),
        delay=0.01,
    )
    runner.set_study_id("test_study")

    result_queue: queue.Queue = queue.Queue()
    runner.set_result_queue(result_queue)

    runner.start(executor)
    time.sleep(0.05)  # Let it process a few items
    runner.close()

    assert runner.is_closed()
    results_count = result_queue.qsize()
    assert results_count < 100  # Should not have processed all items


def test_query_result_single_runner(
    executor: ThreadPoolExecutor,
) -> None:
    """Test QueryResult with a single runner."""
    runner = MockQueryRunner(data=[1, 2, 3])
    runner.set_study_id("test_study")

    result = QueryResult(executor, [runner])
    result.start()

    results = [
        item for item in result if item is not None
    ]

    result.close()
    assert results == [1, 2, 3]


def test_query_result_multiple_runners(
    executor: ThreadPoolExecutor,
) -> None:
    """Test QueryResult with multiple runners."""
    runner1 = MockQueryRunner(data=[1, 2, 3])
    runner1.set_study_id("study1")

    runner2 = MockQueryRunner(data=[4, 5, 6])
    runner2.set_study_id("study2")

    result = QueryResult(executor, [runner1, runner2])
    result.start()

    results = [
        item for item in result if item is not None
    ]
    result.close()
    assert sorted(results) == [1, 2, 3, 4, 5, 6]


def test_query_result_with_limit(
    executor: ThreadPoolExecutor,
) -> None:
    """Test QueryResult with limit parameter."""
    runner = MockQueryRunner(data=list(range(10)))
    runner.set_study_id("test_study")

    result = QueryResult(executor, [runner], limit=5)
    result.start()

    results = [
        item for item in result if item is not None
    ]

    result.close()
    assert len(results) == 5
    assert results == [0, 1, 2, 3, 4]


def test_query_result_get_method(
    executor: ThreadPoolExecutor,
) -> None:
    """Test QueryResult.get() method."""
    runner = MockQueryRunner(data=[1, 2, 3], delay=0.01)
    runner.set_study_id("test_study")

    result = QueryResult(executor, [runner])
    result.start()

    results = []
    while True:
        try:
            item = result.get(timeout=0.1)
            if item is not None:
                results.append(item)
        except StopIteration:
            break

    result.close()
    assert results == [1, 2, 3]


def test_query_result_is_done(
    executor: ThreadPoolExecutor,
) -> None:
    """Test QueryResult.is_done() method."""
    runner = MockQueryRunner(data=[1, 2, 3], delay=0.01)
    runner.set_study_id("test_study")

    result = QueryResult(executor, [runner])

    assert not result.is_done()

    result.start()
    time.sleep(0.05)

    # Wait for completion
    for _ in result:
        pass

    assert result.is_done()
    result.close()


def test_query_result_exception_handling(
    executor: ThreadPoolExecutor,
) -> None:
    """Test QueryResult handles exceptions from runners."""

    class FailingRunner(QueryRunner):
        def run(self) -> None:
            self.put_value_in_result_queue(ValueError("Test error"))
            with self._status_lock:
                self._done = True

    runner = FailingRunner()
    runner.set_study_id("failing_study")

    result = QueryResult(executor, [runner])
    result.start()

    # Consume results
    for _ in result:
        pass

    assert len(result._exceptions) == 1
    assert isinstance(result._exceptions[0], ValueError)

    with pytest.raises(OSError, match="Test error"):
        result.close()


def test_query_result_empty_runners(
    executor: ThreadPoolExecutor,
) -> None:
    """Test QueryResult with runners that return no data."""
    runner = MockQueryRunner(data=[])
    runner.set_study_id("empty_study")

    result = QueryResult(executor, [runner])
    result.start()

    results = [
        item for item in result if item is not None
    ]

    result.close()
    assert results == []


def test_query_result_close_before_start(
    executor: ThreadPoolExecutor,
) -> None:
    """Test closing QueryResult before starting."""
    runner = MockQueryRunner(data=[1, 2, 3])
    runner.set_study_id("test_study")

    result = QueryResult(executor, [runner])

    # Close before starting should not raise an error
    result.close()

    # Verify the runner is closed
    assert runner.is_closed()


def test_query_runner_put_value_backpressure(
    executor: ThreadPoolExecutor,
) -> None:
    """Test QueryRunner backpressure with small queue."""
    runner = MockQueryRunner(data=list(range(10)))
    runner.set_study_id("test_study")

    # Create a small queue to test backpressure
    small_queue: queue.Queue = queue.Queue(maxsize=2)
    runner.set_result_queue(small_queue)

    runner.start(executor)

    # Let the queue fill up
    time.sleep(0.05)

    # Queue should have items
    assert not small_queue.empty()

    # Drain the queue
    while not small_queue.empty():
        small_queue.get()

    time.sleep(0.1)
    runner.close()


def test_multiple_runners_with_different_delays(
    executor: ThreadPoolExecutor,
) -> None:
    """Test multiple runners with different execution delays."""
    runner1 = MockQueryRunner(data=[1, 2, 3], delay=0.01)
    runner1.set_study_id("slow_study")

    runner2 = MockQueryRunner(data=[4, 5, 6], delay=0.0)
    runner2.set_study_id("fast_study")

    runner3 = MockQueryRunner(data=[7, 8, 9], delay=0.005)
    runner3.set_study_id("medium_study")

    result = QueryResult(executor, [runner1, runner2, runner3])
    result.start()

    results = [
        item for item in result if item is not None
    ]

    result.close()
    assert sorted(results) == [1, 2, 3, 4, 5, 6, 7, 8, 9]
    assert len(results) == 9


def test_multiple_runners_with_different_deserializers(
    executor: ThreadPoolExecutor,
) -> None:
    """Test multiple runners with different deserializers."""
    runner1 = MockQueryRunner(
        data=[1, 2, 3],
        deserializer=lambda x: x * 10,
    )
    runner1.set_study_id("study1")

    runner2 = MockQueryRunner(
        data=[4, 5, 6],
        deserializer=lambda x: x * 100,
    )
    runner2.set_study_id("study2")

    result = QueryResult(executor, [runner1, runner2])
    result.start()

    results = [
        item for item in result if item is not None
    ]

    result.close()
    assert sorted(results) == [10, 20, 30, 400, 500, 600]


def test_multiple_runners_one_fails(
    executor: ThreadPoolExecutor,
) -> None:
    """Test multiple runners where one fails."""

    class FailingRunner(QueryRunner):
        def run(self) -> None:
            self.put_value_in_result_queue(RuntimeError("Intentional error"))
            with self._status_lock:
                self._done = True

    runner1 = MockQueryRunner(data=[1, 2, 3])
    runner1.set_study_id("good_study1")

    runner2 = FailingRunner()
    runner2.set_study_id("failing_study")

    runner3 = MockQueryRunner(data=[4, 5, 6])
    runner3.set_study_id("good_study2")

    result = QueryResult(executor, [runner1, runner2, runner3])
    result.start()

    results = [
        item for item in result if item is not None
    ]

    # Should get results from the non-failing runners
    assert sorted(results) == [1, 2, 3, 4, 5, 6]

    # Should have one exception
    assert len(result._exceptions) == 1
    assert isinstance(result._exceptions[0], RuntimeError)

    with pytest.raises(OSError, match="Intentional error"):
        result.close()


def test_multiple_runners_with_limit_reaches_first(
    executor: ThreadPoolExecutor,
) -> None:
    """Test that limit stops all runners when reached."""
    runner1 = MockQueryRunner(data=list(range(100)), delay=0.001)
    runner1.set_study_id("study1")

    runner2 = MockQueryRunner(data=list(range(100, 200)), delay=0.001)
    runner2.set_study_id("study2")

    runner3 = MockQueryRunner(data=list(range(200, 300)), delay=0.001)
    runner3.set_study_id("study3")

    result = QueryResult(executor, [runner1, runner2, runner3], limit=10)
    result.start()

    results = [
        item for item in result if item is not None
    ]

    result.close()
    assert len(results) == 10


def test_multiple_runners_with_empty_and_non_empty(
    executor: ThreadPoolExecutor,
) -> None:
    """Test multiple runners where some return no data."""
    runner1 = MockQueryRunner(data=[])
    runner1.set_study_id("empty_study1")

    runner2 = MockQueryRunner(data=[1, 2, 3])
    runner2.set_study_id("data_study")

    runner3 = MockQueryRunner(data=[])
    runner3.set_study_id("empty_study2")

    result = QueryResult(executor, [runner1, runner2, runner3])
    result.start()

    results = [
        item for item in result if item is not None
    ]

    result.close()
    assert results == [1, 2, 3]


def test_multiple_runners_early_close_all(
    executor: ThreadPoolExecutor,
) -> None:
    """Test closing result early stops all runners."""
    runner1 = MockQueryRunner(data=list(range(100)), delay=0.01)
    runner1.set_study_id("study1")

    runner2 = MockQueryRunner(data=list(range(100, 200)), delay=0.01)
    runner2.set_study_id("study2")

    runner3 = MockQueryRunner(data=list(range(200, 300)), delay=0.01)
    runner3.set_study_id("study3")

    result = QueryResult(executor, [runner1, runner2, runner3])
    result.start()

    # Let them process a few items
    time.sleep(0.05)

    result.close()

    # All runners should be closed
    assert runner1.is_closed()
    assert runner2.is_closed()
    assert runner3.is_closed()

    # Should not have processed all items
    results_count = result.result_queue.qsize()
    assert results_count < 300


def test_multiple_runners_with_adapters(
    executor: ThreadPoolExecutor,
) -> None:
    """Test multiple runners with different adapter chains."""
    runner1 = MockQueryRunner(
        data=[1, 2, 3],
        deserializer=lambda x: x * 2,
    )
    runner1.set_study_id("study1")
    runner1.adapt(lambda x: x + 1)  # (x * 2) + 1

    runner2 = MockQueryRunner(
        data=[4, 5, 6],
        deserializer=lambda x: x * 3,
    )
    runner2.set_study_id("study2")
    runner2.adapt(lambda x: x - 1)  # (x * 3) - 1

    result = QueryResult(executor, [runner1, runner2])
    result.start()

    results = [
        item for item in result if item is not None
    ]

    result.close()
    # runner1-> [3, 5, 7]  (1*2+1, 2*2+1, 3*2+1)
    # runner2-> [11, 14, 17]  (4*3-1, 5*3-1, 6*3-1)
    assert sorted(results) == [3, 5, 7, 11, 14, 17]


def test_multiple_runners_large_number(
    executor: ThreadPoolExecutor,
) -> None:
    """Test with many runners to verify thread pool handling."""
    runners = []
    expected_total = 0

    for i in range(10):
        data = list(range(i * 10, (i + 1) * 10))
        runner = MockQueryRunner(data=data, delay=0.001)
        runner.set_study_id(f"study_{i}")
        runners.append(runner)
        expected_total += len(data)

    result = QueryResult(executor, runners)
    result.start()

    results = [
        item for item in result if item is not None
    ]

    result.close()
    assert len(results) == expected_total
    assert sorted(results) == list(range(100))


def test_multiple_runners_custom_queue_size(
    executor: ThreadPoolExecutor,
) -> None:
    """Test multiple runners with custom queue size."""
    runner1 = MockQueryRunner(data=[1, 2, 3])
    runner1.set_study_id("study1")

    runner2 = MockQueryRunner(data=[4, 5, 6])
    runner2.set_study_id("study2")

    # Create result with small queue
    result = QueryResult(executor, [runner1, runner2], max_queue_size=10)
    result.start()

    results = [
        item for item in result if item is not None
    ]

    result.close()
    assert sorted(results) == [1, 2, 3, 4, 5, 6]
    assert result.result_queue.maxsize == 10


def test_multiple_runners_sequential_completion(
    executor: ThreadPoolExecutor,
) -> None:
    """Test that runners can complete at different times."""
    # Fast runner completes first
    runner1 = MockQueryRunner(data=[1, 2], delay=0.0)
    runner1.set_study_id("fast_study")

    # Slow runner completes last
    runner2 = MockQueryRunner(data=[3, 4, 5, 6], delay=0.05)
    runner2.set_study_id("slow_study")

    result = QueryResult(executor, [runner1, runner2])
    result.start()

    # Fast runner should complete quickly
    time.sleep(0.02)
    assert runner1.is_done()
    assert not runner2.is_done()

    # Wait for slow runner
    results = [
        item for item in result if item is not None
    ]

    assert runner2.is_done()
    result.close()
    assert sorted(results) == [1, 2, 3, 4, 5, 6]


def test_multiple_runners_none_filtering(
    executor: ThreadPoolExecutor,
) -> None:
    """Test that None values from deserializers are handled correctly."""

    def filter_even(x: int) -> int | None:
        return x if x % 2 == 0 else None

    runner1 = MockQueryRunner(
        data=[1, 2, 3, 4, 5],
        deserializer=filter_even,
    )
    runner1.set_study_id("study1")

    runner2 = MockQueryRunner(
        data=[6, 7, 8, 9, 10],
        deserializer=filter_even,
    )
    runner2.set_study_id("study2")

    result = QueryResult(executor, [runner1, runner2])
    result.start()

    # The iterator returns None when queue is empty but not done
    # We collect all non-None items
    results = [
        item for item in result if item is not None
    ]

    result.close()
    # Should only get even numbers
    assert sorted(results) == [2, 4, 6, 8, 10]
