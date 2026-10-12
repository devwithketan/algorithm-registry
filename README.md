# algorithm-registry

Generic, type-safe **Strategy + Registry**, **Factory** and **Singleton**
building blocks for interchangeable algorithms, generalised from
`pycomets/road_geometry/curvature/algorithms.py`.

```python
smoothers.create("moving_average", window=5).compute(signal)
factory.from_config({"method": "moving_average", "params": {"window": 5}})
```

## Layout

```text
src/algorithm_registry/algorithm.py   # Strategy + Registry (stdlib only, copy-pasteable)
src/algorithm_registry/factory.py     # Factory: defaults, param validation, config parsing
src/algorithm_registry/singleton.py   # Singleton metaclass (standalone)
examples/smoothing.py                 # example family: 1-D signal smoothers
examples/factory_example.py           # building smoothers from defaults/config
examples/singleton_example.py         # shared calibration table injected into an algorithm
tests/                                # tests for every module and example
USAGE.md                              # how to use, extend, test and migrate
```

## Quick start

```bash
uv sync
uv run python examples/smoothing.py
uv run python examples/factory_example.py
uv run python examples/singleton_example.py
uv run pytest
```

See [USAGE.md](USAGE.md) for the full guide.
