import re
import math


class AbstractAggregator:
    def __init__(self):
        self.total_count = 0
        self.used_count = 0

    def __call__(self):
        return self.get_final()

    def add(self, v):
        self.total_count += 1
        self._add_internal(v)

    def _add_internal(self, v):
        raise NotImplementedError()

    def clear(self):
        self.total_count = 0
        self.used_count = 0
        self._clear_internal()

    def _clear_internal(self):
        raise NotImplementedError()

    def get_final(self):
        raise NotImplementedError()

    def get_total_count(self):
        return self.total_count

    def get_used_count(self):
        return self.used_count

    def __eq__(self, o: object) -> bool:
        return self.get_final() == o


class MaxAggregator(AbstractAggregator):
    def __init__(self):
        super().__init__()
        self.current_max = None

    def _add_internal(self, v):
        if v is None:
            return
        if self.current_max is not None:
            self.current_max = max(self.current_max, v)
        else:
            self.current_max = v

        self.used_count += 1

    def _clear_internal(self):
        self.current_max = None

    def get_final(self):
        return self.current_max


class MinAggregator(AbstractAggregator):
    def __init__(self):
        super().__init__()
        self.current_min = None

    def _add_internal(self, v):
        if v is None:
            return
        if self.current_min is not None:
            self.current_min = min(self.current_min, v)
        else:
            self.current_min = v

        self.used_count += 1

    def _clear_internal(self):
        self.current_min = None

    def get_final(self):
        return self.current_min


class MeanAggregator(AbstractAggregator):
    def __init__(self):
        super().__init__()
        self.sum = 0

    def _add_internal(self, v):
        if v is None:
            return

        self.sum += v
        self.used_count += 1

    def _clear_internal(self):
        self.sum = 0

    def get_final(self):
        if self.used_count > 0:
            return self.sum / self.used_count
        return None


class ConcatAggregator(AbstractAggregator):
    def __init__(self):
        super().__init__()
        self.out = ""

    def _add_internal(self, v):
        if v is not None:
            self.out += str(v)
            self.used_count += 1

    def _clear_internal(self):
        self.out = ""

    def get_final(self):
        if self.out == "":
            return None

        return self.out


class MedianAggregator(AbstractAggregator):
    def __init__(self):
        super().__init__()
        self.values = list()

    def _add_internal(self, v):
        if v is not None:
            self.values.append(v)
            self.used_count += 1

    def _clear_internal(self):
        self.values.clear()

    def get_final(self):
        self.values.sort()
        print(self.values)
        if len(self.values) % 2 == 1:
            return self.values[math.floor(len(self.values)/2)]
        else:
            first = self.values[int(len(self.values)/2)-1]
            second = self.values[int(len(self.values)/2)]
            if isinstance(first, str):
                assert isinstance(second, str)
                return first + second
            else:
                return (first + second) / 2


class ModeAggregator(AbstractAggregator):
    def __init__(self):
        super().__init__()
        self.value_counts = dict()

    def _add_internal(self, v):
        if v is not None:
            if v not in self.value_counts:
                self.value_counts[v] = 0
            self.value_counts[v] += 1
            self.used_count += 1

    def _clear_internal(self):
        self.value_counts.clear()

    def get_final(self):
        count_values = dict()
        current_max = None
        for value, count in self.value_counts.items():
            if count not in count_values:
                count_values[count] = list()

            count_values[count].append(value)

            if current_max is None:
                current_max = count
            elif current_max < count:
                current_max = count
        modes = count_values[current_max]
        modes.sort()
        return modes[0]


class JoinAggregator(AbstractAggregator):
    def __init__(self, separator):
        super().__init__()
        self.values = list()
        self.separator = separator

    def _add_internal(self, v):
        if v is not None:
            self.values.append(str(v))
            self.used_count += 1

    def _clear_internal(self):
        self.values.clear()

    def get_final(self):
        return self.separator.join(self.values)


AGGREGATOR_CLASS_DICT = {
    "max": MaxAggregator,
    "min": MinAggregator,
    "mean": MeanAggregator,
    "concatenate": ConcatAggregator,
    "median": MedianAggregator,
    "mode": ModeAggregator,
    "join": JoinAggregator
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
    ],
}


def get_aggregator_class(aggregator):
    return AGGREGATOR_CLASS_DICT[aggregator]


def create_aggregator_definition(aggregator_type):
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


def create_aggregator(aggregator_def):
    aggregator_name = aggregator_def["name"]
    aggregator_class = get_aggregator_class(aggregator_name)
    if "args" in aggregator_def:
        return aggregator_class(*aggregator_def["args"])
    else:
        return aggregator_class()


def build_aggregator(aggregator_type):
    aggregator_def = create_aggregator_definition(aggregator_type)
    return create_aggregator(aggregator_def)
