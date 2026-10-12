"""Singleton pattern: at most one lazily created, thread-safe instance per class.

Prefer a module-level instance (like the ``smoothers`` registry) or dependency
injection. Use :class:`SingletonMeta` only when a class itself must guarantee
a single process-wide instance, e.g. an expensive shared resource, and inject
that instance into its consumers rather than calling the class everywhere.

This module is stdlib-only and independent of the rest of the package.
"""

from __future__ import annotations

import inspect
import threading
from abc import ABCMeta
from typing import Any, ClassVar

__all__ = ["SingletonArgumentsError", "SingletonMeta"]


class SingletonArgumentsError(ValueError):
    """A singleton was requested again with different constructor arguments."""


class SingletonMeta(ABCMeta):
    """Metaclass that gives each class exactly one instance.

    * **Lazy** - the instance is built on the first call.
    * **Thread-safe** - double-checked locking; the lock is re-entrant so one
      singleton's ``__init__`` may create another.
    * **Per class** - every subclass gets its own instance.
    * **Explicit** - a later call *with* arguments that differ from the first
      call raises :class:`SingletonArgumentsError` instead of silently
      returning a differently configured object. A call without arguments
      always returns the existing instance.
    * **ABC-compatible** - derives from ``ABCMeta``, so it can be combined with
      abstract bases such as :class:`~algorithm_registry.algorithm.Algorithm`.
    """

    _instances: ClassVar[dict[type, Any]] = {}
    _arguments: ClassVar[dict[type, dict[str, Any]]] = {}
    _lock = threading.RLock()

    def __call__(cls, *args: Any, **kwargs: Any) -> Any:
        instance = SingletonMeta._instances.get(cls)
        if instance is None:
            with SingletonMeta._lock:
                instance = SingletonMeta._instances.get(cls)
                if instance is None:
                    instance = super().__call__(*args, **kwargs)
                    # Store arguments first: the lock-free path reads them after.
                    SingletonMeta._arguments[cls] = _bound_arguments(cls, args, kwargs)
                    SingletonMeta._instances[cls] = instance
                    return instance
        if args or kwargs:
            _ensure_same_arguments(cls, _bound_arguments(cls, args, kwargs))
        return instance

    def reset_instance(cls) -> None:
        """Forget the instance so the next call builds a new one (for tests)."""
        with SingletonMeta._lock:
            SingletonMeta._instances.pop(cls, None)
            SingletonMeta._arguments.pop(cls, None)


def _bound_arguments(
    cls: type, args: tuple[Any, ...], kwargs: dict[str, Any]
) -> dict[str, Any]:
    """Normalise constructor arguments so ``C(3)`` and ``C(size=3)`` compare equal."""
    # signature(cls) would report SingletonMeta.__call__, so read __init__ directly.
    signature = inspect.signature(cls.__init__)  # type: ignore[misc]
    bound = signature.bind(None, *args, **kwargs)  # None stands in for ``self``
    bound.apply_defaults()
    arguments = dict(bound.arguments)
    arguments.pop(next(iter(signature.parameters)))
    return arguments


def _ensure_same_arguments(cls: type, requested: dict[str, Any]) -> None:
    existing = SingletonMeta._arguments[cls]
    differing = sorted(
        key
        for key in existing.keys() | requested.keys()
        if existing.get(key) != requested.get(key)
    )
    if differing:
        # Only parameter names are reported; values may be sensitive.
        raise SingletonArgumentsError(
            f"{cls.__name__} is a singleton already created with different "
            f"values for {differing}. Call it without arguments to reuse it."
        )
