from dataclasses import dataclass
from typing import Literal

from typing_extensions import TypeAlias

RemoteDefinitionType: TypeAlias = Literal[
    "asset",
    "job",
    "resource",
    "schedule",
    "sensor",
]


@dataclass
class RemoteDefinition:
    name: str
    type: RemoteDefinitionType
