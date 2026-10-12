"""Example algorithm family: interchangeable 1-D signal smoothers.

Run it with ``uv run python examples/smoothing.py``.
"""

from __future__ import annotations

from collections.abc import Sequence

from algorithm_registry import (
    Algorithm,
    AlgorithmConfigurationError,
    AlgorithmInputError,
    AlgorithmRegistry,
)


class SmoothingAlgorithm(Algorithm[Sequence[float], list[float]]):
    """Base class shared by every smoothing algorithm."""


smoothers: AlgorithmRegistry[SmoothingAlgorithm] = AlgorithmRegistry(
    SmoothingAlgorithm, family="smoothing algorithm"
)


@smoothers.register("identity")
class IdentitySmoothing(SmoothingAlgorithm):
    """Return the signal unchanged; useful as a baseline."""

    def compute(self, data: Sequence[float]) -> list[float]:
        return list(data)


@smoothers.register("moving_average")
class MovingAverageSmoothing(SmoothingAlgorithm):
    """Trailing mean over the last ``window`` samples."""

    def __init__(self, window: int = 3) -> None:
        if window < 1:
            raise AlgorithmConfigurationError(f"window must be >= 1, got {window}.")
        self._window = window

    def compute(self, data: Sequence[float]) -> list[float]:
        if len(data) < self._window:
            raise AlgorithmInputError(
                f"moving_average needs at least {self._window} samples "
                f"for window={self._window}, got {len(data)}."
            )
        result: list[float] = []
        for index in range(len(data)):
            chunk = data[max(0, index - self._window + 1) : index + 1]
            result.append(sum(chunk) / len(chunk))
        return result


@smoothers.register("exponential")
class ExponentialSmoothing(SmoothingAlgorithm):
    """Exponentially weighted mean: ``s[i] = alpha * x[i] + (1 - alpha) * s[i-1]``."""

    def __init__(self, alpha: float = 0.5) -> None:
        if not 0.0 < alpha <= 1.0:
            raise AlgorithmConfigurationError(f"alpha must be in (0, 1], got {alpha}.")
        self._alpha = alpha

    def compute(self, data: Sequence[float]) -> list[float]:
        if not data:
            raise AlgorithmInputError("exponential smoothing needs at least 1 sample.")
        result = [float(data[0])]
        for value in data[1:]:
            result.append(self._alpha * value + (1.0 - self._alpha) * result[-1])
        return result


def main() -> None:
    signal = [1.0, 4.0, 2.0, 8.0, 5.0, 7.0]
    for name in smoothers.available():
        print(f"{name:>15}: {smoothers.create(name).compute(signal)}")
    windowed = smoothers.create("moving_average", window=2)
    print(f"{'window=2':>15}: {windowed.compute(signal)}")


if __name__ == "__main__":
    main()
