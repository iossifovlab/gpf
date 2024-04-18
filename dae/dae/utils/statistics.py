from collections.abc import Iterator, MutableMapping
from typing import Any, Dict, Tuple, Union


class StatsCollection(MutableMapping):
    """Helper class for collection of variuos statistics.

    This class would be used in the project in places where collection of
    statistics data about how components of the system work seems appropriate.

    It provides a dict-like interface.

    The keys are tuples of strings. The values could be anything, but usually
    they are numbers.

    >>> stats = StatsCollection()
    >>> stats[("a",)] = 1
    >>> stats[("a",)]
    1
    >>> stats.get(("a", 1))

    The keys a treated as a hierarchy. You can get all values whose key's start
    match the passed key. For example if you add following:
    >>> stats[("b", "1")] = 42
    >>> stats[("b", "2")] = 43

    you can get all values whose keys start with ("b",...) using:
    >>> stats[("b",)]
    {('b', '1'): 42, ('b', '2'): 43}
    """

    def __init__(self) -> None:
        self._stats: Dict[Tuple[str, ...], int] = {}

    def __delitem__(self, key: Tuple[str, ...]) -> None:
        pass

    def __setitem__(self, key: Tuple[str, ...], value: Any) -> None:
        """Store stats value for the specified key."""
        self._stats[key] = value

    def __getitem__(
        self, key: tuple[str, ...],
        default: int = 0,
    ) -> Union[int, dict[tuple[str, ...], int]]:
        """Get stats value corresponding to key or default if not found."""
        result: dict[tuple[str, ...], int] = {}
        for k, v in self._stats.items():
            if k[:len(key)] == key:
                result[k] = v
        if result:
            if len(result) == 1 and key in result:
                return result[key]
            return result  # type: ignore
        return default

    def __iter__(self) -> Iterator[Tuple[str, ...]]:
        return iter(self._stats)

    def __len__(self) -> int:
        return len(self._stats)

    def __repr__(self) -> str:
        return str(self._stats)

    def inc(self, key: Tuple[str, ...]) -> None:
        """Increment stats value for the specified key."""
        self._stats[key] = self._stats.get(key, 0) + 1

    def save(self, filename: str) -> None:
        """Save stats to a file."""
        with open(filename, "wt") as output:
            for k, v in self._stats.items():
                key = ".".join(k)
                output.write(f"{key}\t{v}\n")
