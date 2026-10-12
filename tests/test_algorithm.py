"""Behaviour of the generic AlgorithmRegistry, independent of any family."""

from __future__ import annotations

import pytest

from algorithm_registry import (
    Algorithm,
    AlgorithmAlreadyRegisteredError,
    AlgorithmError,
    AlgorithmNotFoundError,
    AlgorithmRegistry,
    InvalidAlgorithmError,
)


class Scaler(Algorithm[float, float]):
    """Test family: scale a number."""


class Double(Scaler):
    def compute(self, data: float) -> float:
        return data * 2


class Multiply(Scaler):
    def __init__(self, factor: float = 1.0) -> None:
        self.factor = factor

    def compute(self, data: float) -> float:
        return data * self.factor


@pytest.fixture
def scalers() -> AlgorithmRegistry[Scaler]:
    return AlgorithmRegistry(Scaler, family="scaler")


def test_register_returns_class_unchanged(scalers: AlgorithmRegistry[Scaler]) -> None:
    assert scalers.register("double")(Double) is Double
    assert scalers.get("double") is Double


def test_create_forwards_constructor_kwargs(
    scalers: AlgorithmRegistry[Scaler],
) -> None:
    scalers.add("multiply", Multiply)

    algorithm = scalers.create("multiply", factor=3.0)

    assert isinstance(algorithm, Multiply)
    assert algorithm.compute(2.0) == 6.0


def test_available_is_sorted_and_supports_membership(
    scalers: AlgorithmRegistry[Scaler],
) -> None:
    scalers.add("multiply", Multiply)
    scalers.add("double", Double)

    assert scalers.available() == ("double", "multiply")
    assert "double" in scalers
    assert "triple" not in scalers
    assert len(scalers) == 2
    assert "double" in repr(scalers)


def test_duplicate_name_is_rejected(scalers: AlgorithmRegistry[Scaler]) -> None:
    scalers.add("double", Double)

    with pytest.raises(AlgorithmAlreadyRegisteredError, match="double"):
        scalers.add("double", Multiply)


def test_unknown_name_lists_available(scalers: AlgorithmRegistry[Scaler]) -> None:
    scalers.add("double", Double)

    with pytest.raises(AlgorithmNotFoundError, match=r"Available: \['double'\]"):
        scalers.create("triple")


@pytest.mark.parametrize("name", ["", "   "])
def test_blank_name_is_rejected(scalers: AlgorithmRegistry[Scaler], name: str) -> None:
    with pytest.raises(InvalidAlgorithmError, match="blank"):
        scalers.add(name, Double)


def test_non_subclass_is_rejected(scalers: AlgorithmRegistry[Scaler]) -> None:
    with pytest.raises(InvalidAlgorithmError, match="must subclass Scaler"):
        scalers.add("int", int)  # type: ignore[arg-type]


def test_abstract_class_is_rejected(scalers: AlgorithmRegistry[Scaler]) -> None:
    with pytest.raises(InvalidAlgorithmError, match="abstract"):
        scalers.add("scaler", Scaler)  # type: ignore[type-abstract]


def test_registries_are_isolated() -> None:
    first: AlgorithmRegistry[Scaler] = AlgorithmRegistry(Scaler)
    second: AlgorithmRegistry[Scaler] = AlgorithmRegistry(Scaler)

    first.add("double", Double)

    assert "double" not in second


def test_errors_share_a_catchable_root(scalers: AlgorithmRegistry[Scaler]) -> None:
    with pytest.raises(AlgorithmError):
        scalers.get("missing")
    with pytest.raises(LookupError):
        scalers.get("missing")
