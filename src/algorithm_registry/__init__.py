"""Generic, type-safe Strategy, Registry, Factory and Singleton building blocks."""

from __future__ import annotations

from .algorithm import (
    Algorithm,
    AlgorithmAlreadyRegisteredError,
    AlgorithmConfigurationError,
    AlgorithmError,
    AlgorithmInputError,
    AlgorithmNotFoundError,
    AlgorithmRegistry,
    InvalidAlgorithmError,
)
from .factory import AlgorithmFactory, AlgorithmLookup, AlgorithmSpec
from .singleton import SingletonArgumentsError, SingletonMeta

__all__ = [
    "Algorithm",
    "AlgorithmAlreadyRegisteredError",
    "AlgorithmConfigurationError",
    "AlgorithmError",
    "AlgorithmFactory",
    "AlgorithmInputError",
    "AlgorithmLookup",
    "AlgorithmNotFoundError",
    "AlgorithmRegistry",
    "AlgorithmSpec",
    "InvalidAlgorithmError",
    "SingletonArgumentsError",
    "SingletonMeta",
]
