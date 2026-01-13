from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass(frozen=True)
class ControllerConfig:
    controller: str
    username: str
    password: str
    cacert: str
    owner_id: int
    uuid: str
    endpoint: str


@dataclass(frozen=True)
class Cloud:
    name: str


@dataclass(frozen=True)
class ControllerInfo:
    name: str
    uuid: str
    clouds: List[Cloud] = field(default_factory=list)


@dataclass(frozen=True)
class Machine:
    ordinal: int
    ip: Optional[str]
    instance_id: str


@dataclass(frozen=True)
class Unit:
    ordinal: int
    name: str
    machine_instance_id: str


@dataclass(frozen=True)
class Application:
    name: str
    charm: str
    subordinate: bool
    units: List[Unit] = field(default_factory=list)


@dataclass(frozen=True)
class Model:
    uuid: str
    name: str
    owner: str
    controller_uuid: str
    cloud: str
    applications: List[Application] = field(default_factory=list)
    machines: Dict[str, Machine] = field(default_factory=dict)
