"""The smoothing example family built on the generic registry."""

from __future__ import annotations

import pytest
from smoothing import SmoothingAlgorithm, main, smoothers

from algorithm_registry import AlgorithmConfigurationError, AlgorithmInputError

SIGNAL = [1.0, 4.0, 2.0, 8.0]


def test_all_example_algorithms_are_registered() -> None:
    assert smoothers.available() == ("exponential", "identity", "moving_average")


@pytest.mark.parametrize("name", ["exponential", "identity", "moving_average"])
def test_every_algorithm_preserves_length(name: str) -> None:
    algorithm = smoothers.create(name)

    assert isinstance(algorithm, SmoothingAlgorithm)
    assert len(algorithm.compute(SIGNAL)) == len(SIGNAL)


def test_moving_average_uses_trailing_window() -> None:
    result = smoothers.create("moving_average", window=2).compute(SIGNAL)

    assert result == [1.0, 2.5, 3.0, 5.0]


def test_exponential_weights_recent_samples() -> None:
    result = smoothers.create("exponential", alpha=0.5).compute(SIGNAL)

    assert result == [1.0, 2.5, 2.25, 5.125]


@pytest.mark.parametrize(
    ("name", "kwargs"),
    [("moving_average", {"window": 0}), ("exponential", {"alpha": 0.0})],
)
def test_invalid_configuration_fails_at_construction(
    name: str, kwargs: dict[str, float]
) -> None:
    with pytest.raises(AlgorithmConfigurationError):
        smoothers.create(name, **kwargs)


@pytest.mark.parametrize(
    ("name", "data"), [("moving_average", [1.0]), ("exponential", [])]
)
def test_insufficient_input_is_rejected(name: str, data: list[float]) -> None:
    with pytest.raises(AlgorithmInputError):
        smoothers.create(name).compute(data)


def test_demo_runs(capsys: pytest.CaptureFixture[str]) -> None:
    main()

    assert "moving_average" in capsys.readouterr().out
