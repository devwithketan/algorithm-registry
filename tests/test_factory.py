"""Behaviour of AlgorithmFactory and AlgorithmSpec."""

from __future__ import annotations

from typing import Any

import pytest

from algorithm_registry import (
    Algorithm,
    AlgorithmConfigurationError,
    AlgorithmFactory,
    AlgorithmNotFoundError,
    AlgorithmRegistry,
    AlgorithmSpec,
)


class Scaler(Algorithm[float, float]):
    """Test family: scale a number."""


class Double(Scaler):
    def compute(self, data: float) -> float:
        return data * 2


class Affine(Scaler):
    def __init__(self, factor: float = 1.0, *, offset: float = 0.0) -> None:
        self.factor = factor
        self.offset = offset

    def compute(self, data: float) -> float:
        return data * self.factor + self.offset


@pytest.fixture
def registry() -> AlgorithmRegistry[Scaler]:
    scalers: AlgorithmRegistry[Scaler] = AlgorithmRegistry(Scaler, family="scaler")
    scalers.add("double", Double)
    scalers.add("affine", Affine)
    return scalers


@pytest.fixture
def factory(registry: AlgorithmRegistry[Scaler]) -> AlgorithmFactory[Scaler]:
    return AlgorithmFactory(registry, defaults={"affine": {"factor": 3.0}})


def test_defaults_are_applied(factory: AlgorithmFactory[Scaler]) -> None:
    assert factory.create("affine").compute(2.0) == 6.0


def test_overrides_win_over_defaults(factory: AlgorithmFactory[Scaler]) -> None:
    assert factory.create("affine", factor=1.0, offset=1.0).compute(2.0) == 3.0


def test_algorithm_without_defaults(factory: AlgorithmFactory[Scaler]) -> None:
    assert isinstance(factory.create("double"), Double)


def test_unknown_parameter_is_a_configuration_error(
    factory: AlgorithmFactory[Scaler],
) -> None:
    with pytest.raises(AlgorithmConfigurationError, match="offst") as info:
        factory.create("affine", offst=1.0)

    assert isinstance(info.value.__cause__, TypeError)


def test_unknown_name_is_not_found(factory: AlgorithmFactory[Scaler]) -> None:
    with pytest.raises(AlgorithmNotFoundError):
        factory.create("triple")


@pytest.mark.parametrize(
    ("defaults", "error"),
    [
        ({"triple": {}}, AlgorithmNotFoundError),
        ({"affine": {"scale": 2.0}}, AlgorithmConfigurationError),
    ],
)
def test_invalid_defaults_fail_at_construction(
    registry: AlgorithmRegistry[Scaler],
    defaults: dict[str, dict[str, Any]],
    error: type[Exception],
) -> None:
    with pytest.raises(error):
        AlgorithmFactory(registry, defaults=defaults)


def test_defaults_are_copied(registry: AlgorithmRegistry[Scaler]) -> None:
    defaults = {"affine": {"factor": 3.0}}
    factory = AlgorithmFactory(registry, defaults=defaults)

    defaults["affine"]["factor"] = 100.0

    assert factory.create("affine").compute(1.0) == 3.0


def test_from_spec(factory: AlgorithmFactory[Scaler]) -> None:
    spec = AlgorithmSpec("affine", {"offset": 1.0})

    assert factory.from_spec(spec).compute(2.0) == 7.0


def test_from_config(factory: AlgorithmFactory[Scaler]) -> None:
    algorithm = factory.from_config({"method": "affine", "params": {"factor": 2.0}})

    assert algorithm.compute(2.0) == 4.0


def test_from_config_params_are_optional(factory: AlgorithmFactory[Scaler]) -> None:
    assert factory.from_config({"method": "double"}).compute(1.0) == 2.0


@pytest.mark.parametrize(
    ("config", "match"),
    [
        ({"params": {}}, "'method' is required"),
        ({"method": 3}, "'method' is required"),
        ({"method": "affine", "params": [1.0]}, "'params' must be a mapping"),
        ({"method": "affine", "params": {1: 2.0}}, "'params' must be a mapping"),
        ({"method": "affine", "extra": 1}, r"Unknown config keys \['extra'\]"),
    ],
)
def test_malformed_config_is_rejected(
    factory: AlgorithmFactory[Scaler], config: dict[Any, Any], match: str
) -> None:
    with pytest.raises(AlgorithmConfigurationError, match=match):
        factory.from_config(config)


def test_spec_is_immutable() -> None:
    params = {"factor": 2.0}
    spec = AlgorithmSpec("affine", params)

    params["factor"] = 100.0

    assert spec.params == {"factor": 2.0}
    with pytest.raises(TypeError):
        spec.params["factor"] = 5.0  # type: ignore[index]


@pytest.mark.parametrize("name", ["", "  "])
def test_spec_rejects_blank_name(name: str) -> None:
    with pytest.raises(AlgorithmConfigurationError, match="blank"):
        AlgorithmSpec(name)


def test_factory_accepts_any_lookup() -> None:
    class FixedLookup:
        def get(self, name: str) -> type[Scaler]:
            return Double

    factory: AlgorithmFactory[Scaler] = AlgorithmFactory(FixedLookup())

    assert isinstance(factory.create("anything"), Double)
