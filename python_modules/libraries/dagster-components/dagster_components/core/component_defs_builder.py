import importlib
import warnings
from collections.abc import Mapping, Sequence
from pathlib import Path
from types import ModuleType
from typing import TYPE_CHECKING, Optional

from dagster._utils.warnings import suppress_dagster_warnings

from dagster_components.core.component import (
    Component,
    ComponentLoadContext,
    DefinitionsModuleCache,
    discover_entry_point_component_types,
)
from dagster_components.core.component_decl_builder import (
    ComponentDeclNode,
    ComponentFolder,
    YamlComponentDecl,
    path_to_decl_node,
)
from dagster_components.core.component_key import ComponentKey
from dagster_components.utils import get_path_from_module

if TYPE_CHECKING:
    from dagster import Definitions


def resolve_decl_node_to_yaml_decls(decl: ComponentDeclNode) -> list[YamlComponentDecl]:
    if isinstance(decl, YamlComponentDecl):
        return [decl]
    elif isinstance(decl, ComponentFolder):
        leaf_decls = []
        for sub_decl in decl.sub_decls:
            leaf_decls.extend(resolve_decl_node_to_yaml_decls(sub_decl))
        return leaf_decls

    raise NotImplementedError(f"Unknown component type {decl}")


def build_components_from_component_folder(
    context: ComponentLoadContext, path: Path
) -> Sequence[Component]:
    component_folder = path_to_decl_node(path)
    assert isinstance(component_folder, ComponentFolder)
    return component_folder.load(context.for_decl_node(component_folder))


@suppress_dagster_warnings
def defs_from_components(
    *,
    context: ComponentLoadContext,
    components: Sequence[Component],
    resources: Mapping[str, object],
) -> "Definitions":
    from dagster._core.definitions.definitions_class import Definitions

    return Definitions.merge(
        *[
            *[
                c.build_defs(context.with_rendering_scope(c.get_additional_scope()))
                for c in components
            ],
            Definitions(resources=resources),
        ]
    )


# Public method so optional Nones are fine
@suppress_dagster_warnings
def build_component_defs(
    components_root: ModuleType,
    resources: Optional[Mapping[str, object]] = None,
    component_types: Optional[dict[ComponentKey, type[Component]]] = None,
) -> "Definitions":
    """Build a Definitions object for all the component instances in a given code location.

    Args:
        components_root (Path): The path to the components root. This is a directory containing
            subdirectories with component instances.
    """
    from dagster._core.definitions.definitions_class import Definitions

    # For backcompat, allow a path to be passed, even though the signature doesn't support it
    if isinstance(components_root, (Path, str)):
        warnings.warn(
            "Passing a path to build_component_defs is deprecated. Pass a module instead.",
            DeprecationWarning,
        )
        components_root = importlib.import_module(
            f"{Path(components_root).parent.name}.{Path(components_root).name}"
        )

    component_types = component_types or discover_entry_point_component_types()
    components_root_dir = get_path_from_module(components_root)

    all_defs: list[Definitions] = []
    module_cache = DefinitionsModuleCache(resources=resources or {})
    for component_path in components_root_dir.iterdir():
        defs = module_cache.build_defs_from_component_module(
            module=importlib.import_module(f"{components_root.__name__}.{component_path.name}"),
        )
        all_defs.append(defs)
    return Definitions.merge(*all_defs)
