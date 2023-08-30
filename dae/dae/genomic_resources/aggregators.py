from __future__ import annotations

import re
import math
import abc

from typing import cast, Any, Callable, Type


class Aggregator(abc.ABC):
    """Base class for score aggregators."""

    def __init__(self) -> None:
        self.total_count = 0
        self.used_count = 0

    def __call__(self) -> Any:
        return self.get_final()

    def add(self, value: Any, **kwargs: Any) -> None:
        self.total_count += 1
        self._add_internal(value, **kwargs)

    @abc.abstractmethod
    def _add_internal(self, value: Any, **kwargs: Any) -> None:
        raise NotImplementedError()

    def clear(self) -> None:
        self.total_count = 0
        self.used_count = 0
        self._clear_internal()

    @abc.abstractmethod
    def _clear_internal(self) -> None:
        raise NotImplementedError()

    def get_final(self) -> Any:
        raise NotImplementedError()

    def get_total_count(self) -> int:
        return self.total_count

    def get_used_count(self) -> int:
        return self.used_count

    def __eq__(self, obj: object) -> bool:
        return cast(bool, self.get_final() == obj)


class MaxAggregator(Aggregator):
    """Maximum value aggregator for genomic scores."""

    def __init__(self) -> None:
        super().__init__()
        self.current_max = None

    def _add_internal(self, value: Any, **kwargs: Any) -> None:
        if value is None:
            return
        if self.current_max is not None:
            self.current_max = max(value, self.current_max)
        else:
            self.current_max = value

        self.used_count += 1

    def _clear_internal(self) -> None:
        self.current_max = None

    def get_final(self) -> Any:
        return self.current_max


class MinAggregator(Aggregator):
    """Minimum value aggregator for genomic scores."""

    def __init__(self) -> None:
        super().__init__()
        self.current_min = None

    def _add_internal(self, value: Any, **kwargs: Any) -> None:
        if value is None:
            return
        if self.current_min is not None:
            self.current_min = min(self.current_min, value)
        else:
            self.current_min = value

        self.used_count += 1

    def _clear_internal(self) -> None:
        self.current_min = None

    def get_final(self) -> Any:
        return self.current_min


class MeanAggregator(Aggregator):
    """Aggregator for genomic scores that calculates mean value."""

    def __init__(self) -> None:
        super().__init__()
        self.sum = 0

    def _add_internal(self, value: Any, **kwargs: Any) -> None:
        if value is None:
            return

        self.sum += value
        self.used_count += 1

    def _clear_internal(self) -> None:
        self.sum = 0

    def get_final(self) -> Any:
        if self.used_count > 0:
            return self.sum / self.used_count
        return None


class ConcatAggregator(Aggregator):
    """Aggregator that concatenates all passed values."""

    def __init__(self) -> None:
        super().__init__()
        self.out = ""

    def _add_internal(self, value: Any, **kwargs: Any) -> None:
        if value is not None:
            self.out += str(value)
            self.used_count += 1

    def _clear_internal(self) -> None:
        self.out = ""

    def get_final(self) -> Any:
        if self.out == "":
            return None

        return self.out


class MedianAggregator(Aggregator):
    """Aggregator for genomic scores that calculates median value."""

    def __init__(self) -> None:
        super().__init__()
        self.values: list[Any] = []

    def _add_internal(self, value: Any, **kwargs: Any) -> None:
        if value is not None:
            self.values.append(value)
            self.used_count += 1

    def _clear_internal(self) -> None:
        self.values.clear()

    def get_final(self) -> Any:
        self.values.sort()
        print(self.values)
        if len(self.values) % 2 == 1:
            return self.values[math.floor(len(self.values) / 2)]

        first = self.values[int(len(self.values) / 2) - 1]
        second = self.values[int(len(self.values) / 2)]
        if isinstance(first, str):
            assert isinstance(second, str)
            return first + second

        return (first + second) / 2


class ModeAggregator(Aggregator):
    """Aggregator for genomic scores that calculates mode value."""

    def __init__(self) -> None:
        super().__init__()
        self.value_counts: dict[Any, int] = {}

    def _add_internal(self, value: Any, **kwargs: Any) -> None:
        if value is not None:
            if value not in self.value_counts:
                self.value_counts[value] = 0
            self.value_counts[value] += 1
            self.used_count += 1

    def _clear_internal(self) -> None:
        self.value_counts.clear()

    def get_final(self) -> Any:
        count_values: dict[Any, Any] = {}
        current_max = None
        for value, count in self.value_counts.items():
            if count not in count_values:
                count_values[count] = []

            count_values[count].append(value)

            if current_max is None:
                current_max = count
            elif current_max < count:
                current_max = count
        modes = count_values[current_max]
        modes.sort()
        return modes[0]


class JoinAggregator(Aggregator):
    """Aggregator that joins all passed values using a separator."""

    def __init__(self, separator: str):
        super().__init__()
        self.values: list[Any] = []
        self.separator = separator

    def _add_internal(self, value: Any, **kwargs: Any) -> None:
        if value is not None:
            self.values.append(str(value))
            self.used_count += 1

    def _clear_internal(self) -> None:
        self.values.clear()

    def get_final(self) -> Any:
        if len(self.values) > 0:
            return self.separator.join(self.values)
        return None


class ListAggregator(Aggregator):
    """Aggregator that builds a list of all passed values."""

    def __init__(self) -> None:
        super().__init__()
        self.values: list[Any] = []

    def _add_internal(self, value: Any, **kwargs: Any) -> None:
        if value is not None:
            self.values.append(value)
            self.used_count += 1

    def _clear_internal(self) -> None:
        self.values.clear()

    def get_final(self) -> Any:
        return self.values


class DictAggregator(Aggregator):
    """Aggregator that builds a dictionary of all passed values."""

    def __init__(self) -> None:
        super().__init__()
        self.values: dict[Any, Any] = {}

    def _add_internal(self, value: Any, **kwargs: Any) -> None:
        if value is not None:
            self.values[kwargs["key"]] = value
            self.used_count += 1

    def _clear_internal(self) -> None:
        self.values.clear()

    def get_final(self) -> Any:
        return self.values


AGGREGATOR_CLASS_DICT: dict[str, Type[Aggregator]] = {
    "max": MaxAggregator,
    "min": MinAggregator,
    "mean": MeanAggregator,
    "concatenate": ConcatAggregator,
    "median": MedianAggregator,
    "mode": ModeAggregator,
    "join": JoinAggregator,
    "list": ListAggregator,
    "dict": DictAggregator
}

AGGREGATOR_SCHEMA = {
    "type": "string",
    "oneof": [
        {"regex": "^min$"},
        {"regex": "^max$"},
        {"regex": "^mean$"},
        {"regex": "^concatenate$"},
        {"regex": "^median$"},
        {"regex": "^mode$"},
        {"regex": "^join\\(.+\\)$"},
        {"regex": "^list$"},
        {"regex": "^dict$"},
    ],
}


def get_aggregator_class(aggregator: str) -> Callable[[], Aggregator]:
    return AGGREGATOR_CLASS_DICT[aggregator]


def create_aggregator_definition(aggregator_type: str) -> dict[str, Any]:
    """Parse an aggregator definition string."""
    join_regex = r"^(join)\((.+)\)"
    join_match = re.match(join_regex, aggregator_type)
    if join_match is not None:
        separator = join_match.groups()[1]
        return {
            "name": "join",
            "args": [separator]
        }
    return {
        "name": aggregator_type,
    }


def create_aggregator(aggregator_def: dict[str, Any]) -> Aggregator:
    """Create an aggregator by aggregator definition."""
    aggregator_name = aggregator_def["name"]
    aggregator_class = get_aggregator_class(aggregator_name)
    if "args" in aggregator_def:
        return aggregator_class(*aggregator_def["args"])

    return aggregator_class()


def build_aggregator(aggregator_type: str) -> Aggregator:
    aggregator_def = create_aggregator_definition(aggregator_type)
    return create_aggregator(aggregator_def)


def validate_aggregator(aggregator_type: str) -> None:
    try:
        build_aggregator(aggregator_type)
    except Exception as ex:
        raise ValueError(
            f"Incorrect aggregator '{aggregator_type}'", ex) from ex
