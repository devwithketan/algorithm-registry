"""Singleton example: one shared, expensive-to-load calibration table.

The table is a singleton; algorithms receive it by injection, so tests can
still pass their own table without touching the shared instance.

Run it with ``uv run python examples/singleton_example.py``.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import ClassVar

from smoothing import SmoothingAlgorithm

from algorithm_registry import SingletonArgumentsError, SingletonMeta


class CalibrationTable(metaclass=SingletonMeta):
    """Process-wide calibration data; loading is expensive, so it happens once."""

    load_count: ClassVar[int] = 0

    def __init__(self, gain: float = 2.0) -> None:
        type(self).load_count += 1
        self.gain = gain


class CalibratedSmoothing(SmoothingAlgorithm):
    """Scale every sample by the shared calibration gain."""

    def __init__(self, table: CalibrationTable | None = None) -> None:
        self._table = table if table is not None else CalibrationTable()

    def compute(self, data: Sequence[float]) -> list[float]:
        return [value * self._table.gain for value in data]


def main() -> None:
    first = CalibratedSmoothing()
    second = CalibratedSmoothing()

    print("result:", first.compute([1.0, 2.0, 3.0]))
    print("shared table:", CalibrationTable() is CalibrationTable())
    print("loads for 2 algorithms:", CalibrationTable.load_count)
    print("same output:", first.compute([1.0]) == second.compute([1.0]))

    try:
        CalibrationTable(gain=5.0)
    except SingletonArgumentsError as exc:
        print("rejected:", exc)


if __name__ == "__main__":
    main()
