"""Guards the two-surface contract: every tool must be exported.

`mcp_server.register_all` iterates `crewai_custom_tools.__all__`, so a tool
missing from `__all__` is absent from *both* the library surface and MCP. That
drifted once already — 15 `BaseTool` subclasses were reachable only by full
module path — because nothing checked it.
"""

import importlib
import pkgutil

import pytest
from crewai.tools import BaseTool

import crewai_custom_tools
from crewai_custom_tools import mcp_server


def _iter_defined_tool_classes():
    """Yield (module_name, class) for every BaseTool subclass in the package."""
    seen = set()
    for info in pkgutil.walk_packages(
        crewai_custom_tools.__path__, prefix=f"{crewai_custom_tools.__name__}."
    ):
        module = importlib.import_module(info.name)
        for attr in vars(module).values():
            if (
                isinstance(attr, type)
                and issubclass(attr, BaseTool)
                and attr is not BaseTool
                and attr.__module__ == info.name  # defined here, not imported
                and attr not in seen
            ):
                seen.add(attr)
                yield info.name, attr


def test_every_tool_class_is_exported():
    missing = sorted(
        f"{cls.__name__} ({mod})"
        for mod, cls in _iter_defined_tool_classes()
        if cls.__name__ not in crewai_custom_tools.__all__
    )
    assert not missing, (
        "BaseTool subclasses missing from __all__ — they are on neither the "
        "library nor the MCP surface:\n  " + "\n  ".join(missing)
    )


def test_exported_tools_register_with_mcp():
    """Exporting is only half the contract — MCP must be able to register it."""
    registered, skipped = mcp_server.register_all()
    assert not skipped, f"tools skipped during MCP registration: {skipped}"
    assert registered >= len(list(_iter_defined_tool_classes()))


@pytest.mark.parametrize(
    "name",
    [
        "GrampsEnsureSourceTool",
        "GrampsCreateCitationTool",
        "GrampsAttachCitationTool",
        "GrampsAddUrlTool",
        "GrampsAttachMediaTool",
        "GrampsUploadMediaTool",
        "GenealogyCheckPersonTool",
        "GenealogyFindDuplicatesTool",
        "GenealogyResolvePlaceTool",
        "InseeDecesSearchTool",
        "GallicaSearchTool",
        "WikidataSparqlTool",
    ],
)
def test_previously_unexported_tools_are_importable(name):
    """The 15 tools this file was written for; regression-locks the fix."""
    assert hasattr(crewai_custom_tools, name)
