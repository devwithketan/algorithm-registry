"""Factory pattern: build fully configured algorithms from names, specs or config.

:class:`~algorithm_registry.algorithm.AlgorithmRegistry` answers *which class*
is registered under a name. :class:`AlgorithmFactory` owns *how* it is built:
per-algorithm defaults, parameter validation against the constructor
signature, and parsing of plain config mappings (JSON/YAML/TOML) at the system
boundary. The factory depends only on the narrow :class:`AlgorithmLookup`
protocol, so any registry-like object can back it.
"""

from __future__ import annotations

import inspect
from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Generic, Protocol, TypeVar

from .algorithm import Algorithm, AlgorithmConfigurationError

__all__ = ["AlgorithmFactory", "AlgorithmLookup", "AlgorithmSpec"]

ProductT = TypeVar("ProductT", bound="Algorithm[Any, Any]")
ProductT_co = TypeVar("ProductT_co", covariant=True)


class AlgorithmLookup(Protocol[ProductT_co]):
    """Resolves a name to a class; satisfied by ``AlgorithmRegistry``."""

    def get(self, name: str) -> type[ProductT_co]:
        """Return the class registered under *name*.

        Raises:
            AlgorithmNotFoundError: If nothing is registered under *name*.
        """
        ...


@dataclass(frozen=True)
class AlgorithmSpec:
    """Immutable description of one algorithm to build.

    Args:
        name: Registered algorithm name.
        params: Constructor keyword arguments, copied into a read-only mapping.

    Raises:
        AlgorithmConfigurationError: If *name* is blank.
    """

    name: str
    params: Mapping[str, Any] = field(default_factory=dict, hash=False)

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise AlgorithmConfigurationError("Algorithm name must not be blank.")
        object.__setattr__(self, "params", MappingProxyType(dict(self.params)))

    @classmethod
    def from_mapping(
        cls,
        config: Mapping[str, Any],
        *,
        name_key: str = "method",
        params_key: str = "params",
    ) -> AlgorithmSpec:
        """Parse an untrusted mapping such as ``{"method": ..., "params": {...}}``.

        Args:
            config: Raw configuration, e.g. loaded from JSON, YAML or TOML.
            name_key: Key holding the algorithm name.
            params_key: Optional key holding the constructor parameters.

        Returns:
            The validated spec.

        Raises:
            AlgorithmConfigurationError: If keys are unknown or missing, or
                values have the wrong type.
        """
        unknown = sorted(
            str(key) for key in config if key not in {name_key, params_key}
        )
        if unknown:
            raise AlgorithmConfigurationError(
                f"Unknown config keys {unknown}; "
                f"expected '{name_key}' and optional '{params_key}'."
            )
        name = config.get(name_key)
        if not isinstance(name, str):
            raise AlgorithmConfigurationError(
                f"'{name_key}' is required and must be a string, "
                f"got {type(name).__name__}."
            )
        params = config.get(params_key, {})
        if not isinstance(params, Mapping) or not all(
            isinstance(key, str) for key in params
        ):
            raise AlgorithmConfigurationError(
                f"'{params_key}' must be a mapping with string keys."
            )
        return cls(name, params)


class AlgorithmFactory(Generic[ProductT]):
    """Create configured algorithms from names, specs or raw config.

    Args:
        lookup: Resolves names to classes, usually an ``AlgorithmRegistry``.
        defaults: Per-name constructor keyword arguments applied before any
            overrides. Validated eagerly, so a bad default fails at start-up
            rather than on first use.

    Raises:
        AlgorithmNotFoundError: If *defaults* names an unknown algorithm.
        AlgorithmConfigurationError: If *defaults* holds parameters the
            constructor does not accept.
    """

    def __init__(
        self,
        lookup: AlgorithmLookup[ProductT],
        *,
        defaults: Mapping[str, Mapping[str, Any]] | None = None,
    ) -> None:
        self._lookup = lookup
        self._defaults: dict[str, Mapping[str, Any]] = {}
        for name, params in (defaults or {}).items():
            self._validated_class(name, params)
            self._defaults[name] = MappingProxyType(dict(params))

    def create(self, name: str, /, **overrides: Any) -> ProductT:
        """Build *name* with its defaults, overridden by *overrides*.

        Raises:
            AlgorithmNotFoundError: If *name* is not registered.
            AlgorithmConfigurationError: If the merged parameters do not match
                the constructor, or the constructor rejects their values.
        """
        params = {**self._defaults.get(name, {}), **overrides}
        return self._validated_class(name, params)(**params)

    def from_spec(self, spec: AlgorithmSpec) -> ProductT:
        """Build the algorithm described by *spec* (see :meth:`create`)."""
        return self.create(spec.name, **spec.params)

    def from_config(self, config: Mapping[str, Any]) -> ProductT:
        """Parse and build an algorithm from a raw config mapping.

        Raises:
            AlgorithmConfigurationError: If *config* is malformed (see
                :meth:`AlgorithmSpec.from_mapping`) or the parameters are invalid.
            AlgorithmNotFoundError: If the named algorithm is not registered.
        """
        return self.from_spec(AlgorithmSpec.from_mapping(config))

    def _validated_class(self, name: str, params: Mapping[str, Any]) -> type[ProductT]:
        algorithm_class = self._lookup.get(name)
        signature = inspect.signature(algorithm_class)
        try:
            signature.bind(**params)
        except TypeError as exc:
            accepted = signature.replace(return_annotation=inspect.Signature.empty)
            raise AlgorithmConfigurationError(
                f"Invalid parameters {sorted(params)} for '{name}' "
                f"({algorithm_class.__name__}{accepted}): {exc}."
            ) from exc
        return algorithm_class
