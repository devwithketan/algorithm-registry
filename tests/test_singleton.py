"""Behaviour of SingletonMeta."""

from __future__ import annotations

import threading
from concurrent.futures import ThreadPoolExecutor

import pytest

from algorithm_registry import (
    Algorithm,
    AlgorithmRegistry,
    SingletonArgumentsError,
    SingletonMeta,
)


class Config(metaclass=SingletonMeta):
    def __init__(self, size: int = 3, *, name: str = "default") -> None:
        self.size = size
        self.name = name


@pytest.fixture(autouse=True)
def fresh_config() -> None:
    Config.reset_instance()


def test_same_instance_is_returned() -> None:
    assert Config() is Config()


def test_first_call_configures_the_instance() -> None:
    Config(5)

    assert Config().size == 5


def test_equivalent_arguments_are_accepted() -> None:
    first = Config(3)

    assert Config(size=3, name="default") is first


def test_different_arguments_are_rejected_without_leaking_values() -> None:
    Config(3, name="secret-a")

    with pytest.raises(SingletonArgumentsError, match=r"\['name', 'size'\]") as info:
        Config(4, name="secret-b")

    assert "secret" not in str(info.value)


def test_reset_allows_a_new_instance() -> None:
    first = Config(3)
    Config.reset_instance()

    second = Config(4)

    assert second is not first
    assert second.size == 4


def test_failed_construction_is_not_cached() -> None:
    class Flaky(metaclass=SingletonMeta):
        attempts = 0

        def __init__(self) -> None:
            type(self).attempts += 1
            if type(self).attempts == 1:
                raise RuntimeError("transient")

    with pytest.raises(RuntimeError):
        Flaky()

    assert Flaky() is Flaky()


def test_subclasses_get_their_own_instance() -> None:
    class Child(Config):
        pass

    assert Child() is not Config()
    assert Child() is Child()


def test_class_without_init() -> None:
    class Plain(metaclass=SingletonMeta):
        pass

    assert Plain() is Plain()


def test_concurrent_first_access_builds_one_instance() -> None:
    barrier = threading.Barrier(8)

    class Slow(metaclass=SingletonMeta):
        builds = 0

        def __init__(self) -> None:
            type(self).builds += 1

    def build(_: int) -> Slow:
        barrier.wait()
        return Slow()

    with ThreadPoolExecutor(max_workers=8) as pool:
        instances = list(pool.map(build, range(8)))

    assert Slow.builds == 1
    assert all(instance is instances[0] for instance in instances)


def test_nested_singletons_do_not_deadlock() -> None:
    class Inner(metaclass=SingletonMeta):
        pass

    class Outer(metaclass=SingletonMeta):
        def __init__(self) -> None:
            self.inner = Inner()

    assert Outer().inner is Inner()


def test_works_with_abstract_algorithms_and_registry() -> None:
    class Scaler(Algorithm[float, float]):
        pass

    class SharedDouble(Scaler, metaclass=SingletonMeta):
        def compute(self, data: float) -> float:
            return data * 2

    registry: AlgorithmRegistry[Scaler] = AlgorithmRegistry(Scaler)
    registry.add("double", SharedDouble)

    assert registry.create("double") is registry.create("double")
    assert registry.create("double").compute(2.0) == 4.0
