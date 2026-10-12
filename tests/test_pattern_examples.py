"""The factory and singleton examples run end to end."""

from __future__ import annotations

import factory_example
import pytest
import singleton_example
from singleton_example import CalibratedSmoothing, CalibrationTable


@pytest.fixture(autouse=True)
def fresh_table() -> None:
    CalibrationTable.reset_instance()
    CalibrationTable.load_count = 0


def test_factory_example_runs(capsys: pytest.CaptureFixture[str]) -> None:
    factory_example.main()

    output = capsys.readouterr().out
    assert "default window=2: [1.0, 2.5, 3.0, 5.0, 6.5, 6.0]" in output
    assert "rejected:" in output
    assert "windw" in output


def test_singleton_example_loads_table_once(
    capsys: pytest.CaptureFixture[str],
) -> None:
    singleton_example.main()

    output = capsys.readouterr().out
    assert CalibrationTable.load_count == 1
    assert "shared table: True" in output
    assert "rejected:" in output


def test_default_table_is_the_shared_singleton() -> None:
    CalibrationTable(gain=10.0)

    assert CalibratedSmoothing().compute([1.0]) == [10.0]


def test_injected_table_bypasses_the_shared_singleton() -> None:
    class FakeTable(CalibrationTable):
        pass

    algorithm = CalibratedSmoothing(FakeTable(gain=3.0))

    assert algorithm.compute([1.0]) == [3.0]
    assert CalibrationTable().gain == 2.0
