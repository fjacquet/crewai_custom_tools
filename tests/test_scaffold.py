import tomllib
from pathlib import Path

import pytest

import crewai_custom_tools

PYPROJECT = Path(__file__).resolve().parent.parent / "pyproject.toml"


def test_version_is_a_release_string():
    assert crewai_custom_tools.__version__.count(".") == 2


def test_version_matches_pyproject():
    """__version__ and pyproject's version are bumped in lockstep.

    Asserting a hardcoded literal here silently ratified five bumps of
    pyproject.toml that never reached __init__.py, so this compares the two
    sources instead of pinning either one.
    """
    if not PYPROJECT.is_file():
        pytest.skip("pyproject.toml unavailable (installed package, not a source tree)")

    declared = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))["project"]["version"]
    assert crewai_custom_tools.__version__ == declared
