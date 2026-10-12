"""Factory example: build configured smoothers from defaults and plain config.

Run it with ``uv run python examples/factory_example.py``.
"""

from __future__ import annotations

from smoothing import SmoothingAlgorithm, smoothers

from algorithm_registry import AlgorithmConfigurationError, AlgorithmFactory

factory: AlgorithmFactory[SmoothingAlgorithm] = AlgorithmFactory(
    smoothers,
    defaults={"moving_average": {"window": 2}, "exponential": {"alpha": 0.3}},
)


def main() -> None:
    signal = [1.0, 4.0, 2.0, 8.0, 5.0, 7.0]

    print("default window=2:", factory.create("moving_average").compute(signal))
    print(
        "override window=4:", factory.create("moving_average", window=4).compute(signal)
    )

    config = {"method": "exponential", "params": {"alpha": 0.8}}  # e.g. from JSON/YAML
    print("from config:", factory.from_config(config).compute(signal))

    try:
        factory.from_config({"method": "moving_average", "params": {"windw": 3}})
    except AlgorithmConfigurationError as exc:
        print("rejected:", exc)


if __name__ == "__main__":
    main()
