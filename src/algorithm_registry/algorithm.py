"""Generic, type-safe Strategy + Registry for interchangeable algorithms.

Generalises ``pycomets.road_geometry.curvature.algorithms``: instead of a
hard-coded ``CurvatureAlgorithm`` interface and one class-level registry, the
interface is generic over its input/output types and every algorithm family
owns its own :class:`AlgorithmRegistry` instance.

The module is stdlib-only and self-contained, so it can be copied as-is into
any project.
"""

from __future__ import annotations

import inspect
from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any, Generic, TypeVar

__all__ = [
    "Algorithm",
    "AlgorithmAlreadyRegisteredError",
    "AlgorithmConfigurationError",
    "AlgorithmError",
    "AlgorithmInputError",
    "AlgorithmNotFoundError",
    "AlgorithmRegistry",
    "InvalidAlgorithmError",
]

InputT = TypeVar("InputT", contravariant=True)
OutputT = TypeVar("OutputT", covariant=True)
AlgorithmT = TypeVar("AlgorithmT", bound="Algorithm[Any, Any]")


class AlgorithmError(Exception):
    """Root of every algorithm and registry failure."""


class AlgorithmNotFoundError(AlgorithmError, LookupError):
    """No algorithm is registered under the requested name."""


class AlgorithmAlreadyRegisteredError(AlgorithmError, ValueError):
    """A second algorithm tried to claim a name that is already taken."""


class InvalidAlgorithmError(AlgorithmError, TypeError):
    """The name or class offered for registration is not acceptable."""


class AlgorithmConfigurationError(AlgorithmError, ValueError):
    """An algorithm was constructed with invalid parameters."""


class AlgorithmInputError(AlgorithmError, ValueError):
    """An algorithm received input it cannot process (e.g. too few samples)."""


class Algorithm(ABC, Generic[InputT, OutputT]):
    """One interchangeable way of turning an ``InputT`` into an ``OutputT``.

    Configuration belongs in ``__init__`` (keyword arguments are forwarded by
    :meth:`AlgorithmRegistry.create`) and should be validated there, so bad
    configuration fails before any data is processed. ``compute`` should be
    free of side effects.
    """

    @abstractmethod
    def compute(self, data: InputT) -> OutputT:
        """Run the algorithm on *data*.

        Args:
            data: Input to process.

        Returns:
            The algorithm's result.

        Raises:
            AlgorithmInputError: If *data* cannot be processed.
        """


class AlgorithmRegistry(Generic[AlgorithmT]):
    """Factory and registry mapping unique names to algorithm classes.

    Each algorithm family creates its own instance, so families never share
    state and tests can build isolated registries without any cleanup.

    The family type is taken from the annotation, e.g.
    ``registry: AlgorithmRegistry[MyBase] = AlgorithmRegistry(MyBase)``.

    Args:
        base: Class every registered algorithm must subclass.
        family: Human-readable label used in error messages.
    """

    # Plain ``type``: mypy forbids abstract classes for ``type[AlgorithmT]``.
    def __init__(self, base: type, *, family: str = "algorithm") -> None:
        self._base = base
        self._family = family
        self._entries: dict[str, type[AlgorithmT]] = {}

    def register(self, name: str) -> Callable[[type[AlgorithmT]], type[AlgorithmT]]:
        """Return a class decorator that registers the class under *name*.

        Args:
            name: Unique, non-blank lookup key.

        Returns:
            A decorator that registers the class and returns it unchanged.

        Raises:
            InvalidAlgorithmError: If *name* is blank or the class is not a
                concrete subclass of the registry's base.
            AlgorithmAlreadyRegisteredError: If *name* is already taken.
        """

        def decorator(algorithm_class: type[AlgorithmT]) -> type[AlgorithmT]:
            self.add(name, algorithm_class)
            return algorithm_class

        return decorator

    def add(self, name: str, algorithm_class: type[AlgorithmT]) -> None:
        """Register *algorithm_class* under *name* without a decorator.

        Args:
            name: Unique, non-blank lookup key.
            algorithm_class: Concrete subclass of the registry's base.

        Raises:
            InvalidAlgorithmError: If *name* is blank or *algorithm_class* is
                not a concrete subclass of the registry's base.
            AlgorithmAlreadyRegisteredError: If *name* is already taken.
        """
        if not name.strip():
            raise InvalidAlgorithmError(f"{self._family} name must not be blank.")
        if not isinstance(algorithm_class, type) or not issubclass(
            algorithm_class, self._base
        ):
            raise InvalidAlgorithmError(
                f"{algorithm_class!r} must subclass {self._base.__name__} "
                f"to be registered as {self._family} '{name}'."
            )
        if inspect.isabstract(algorithm_class):
            raise InvalidAlgorithmError(
                f"{algorithm_class.__name__} is abstract and cannot be registered "
                f"as {self._family} '{name}'."
            )
        if name in self._entries:
            raise AlgorithmAlreadyRegisteredError(
                f"{self._family} '{name}' is already registered "
                f"by {self._entries[name].__name__}."
            )
        self._entries[name] = algorithm_class

    def get(self, name: str) -> type[AlgorithmT]:
        """Return the class registered under *name* without instantiating it.

        Raises:
            AlgorithmNotFoundError: If nothing is registered under *name*.
        """
        try:
            return self._entries[name]
        except KeyError as exc:
            raise AlgorithmNotFoundError(
                f"{self._family} '{name}' not found. "
                f"Available: {list(self.available())}"
            ) from exc

    def create(self, name: str, /, **kwargs: Any) -> AlgorithmT:
        """Instantiate the algorithm registered under *name*.

        Args:
            name: Registered lookup key.
            **kwargs: Forwarded to the algorithm's constructor.

        Returns:
            A new instance of the registered algorithm.

        Raises:
            AlgorithmNotFoundError: If nothing is registered under *name*.
            AlgorithmConfigurationError: If the constructor rejects *kwargs*.
        """
        return self.get(name)(**kwargs)

    def available(self) -> tuple[str, ...]:
        """Return the registered names in sorted order."""
        return tuple(sorted(self._entries))

    def __contains__(self, name: object) -> bool:
        return name in self._entries

    def __len__(self) -> int:
        return len(self._entries)

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}(base={self._base.__name__}, "
            f"entries={list(self.available())})"
        )
