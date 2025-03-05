from typing import Literal, TypedDict

from typing_extensions import TypeAlias

RemoteDefinitionType: TypeAlias = Literal[
    "asset",
    "job",
    "resource",
    "schedule",
    "sensor",
]


class RemoteDefinitionMetadata(TypedDict):
    name: str
    type: RemoteDefinitionType
