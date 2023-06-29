"""Core job makers for FHI-aims workflows"""

from dataclasses import dataclass, field

from fhi_aims_workflows.jobs.base import BaseAimsMaker
from fhi_aims_workflows.sets.base import AimsInputGenerator
from fhi_aims_workflows.sets.core import StaticSetGenerator, RelaxSetGenerator
from fhi_aims_workflows.sets.bs import BandStructureSetGenerator, GWSetGenerator


@dataclass
class StaticMaker(BaseAimsMaker):
    """A job Maker for a static calculation"""
    name: str = "static"
    input_set_generator: AimsInputGenerator = field(default_factory=StaticSetGenerator)


@dataclass
class RelaxMaker(BaseAimsMaker):
    """A job Maker for a relax calculation"""
    name: str = "relax"
    input_set_generator: AimsInputGenerator = field(default_factory=RelaxSetGenerator)


@dataclass
class BandStructureMaker(BaseAimsMaker):
    """A job Maker for a band structure calculation"""
    name: str = "bands"
    input_set_generator: AimsInputGenerator = field(default_factory=BandStructureSetGenerator)


@dataclass
class GWMaker(BaseAimsMaker):
    """A job Maker for a GW band structure calculation"""
    name: str = "GW"
    input_set_generator: AimsInputGenerator = field(default_factory=GWSetGenerator)
