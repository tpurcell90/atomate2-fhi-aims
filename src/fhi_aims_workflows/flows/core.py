""" (Work)flows for FHI-aims
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

from jobflow import Maker, Flow

from fhi_aims_workflows.jobs.base import BaseAimsMaker
from fhi_aims_workflows.jobs.core import RelaxMaker
from fhi_aims_workflows.utils.MSONableAtoms import MSONableAtoms


__all__ = ["DoubleRelaxMaker", ]


@dataclass
class DoubleRelaxMaker(Maker):
    """ A maker to perform a double relaxation in FHI-aims (first with light, and then with tight species_defaults)

    Parameters
    ----------
    name : str
        A name for the flow
    relax_maker1: .BaseAimsMaker
        A maker that generates the first relaxation
    relax_maker2: .BaseAimsMaker
        A maker that generates the second relaxation
    """
    name: str = "double relax"
    relax_maker1: BaseAimsMaker = field(default_factory=RelaxMaker)
    relax_maker2: BaseAimsMaker = field(default_factory=RelaxMaker)

    def make(self, structure: MSONableAtoms, prev_dir: str | Path | None = None):
        """
        Create a flow with two chained relaxations.

        Parameters
        ----------
        structure : .MSONableAtoms
            An MSON-able ASE Atoms structure object.
        prev_dir : str or Path or None
            A previous FHI-aims calculation directory to copy output files from.

        Returns
        -------
        Flow
            A flow containing two relaxations.
        """
        relax1 = self.relax_maker1.make(structure, prev_dir=prev_dir)
        relax1.name += " 1"

        relax2 = self.relax_maker2.make(relax1.output.structure, prev_dir=relax1.output.dir_name)
        relax2.name += " 2"

        return Flow([relax1, relax2], relax2.output, name=self.name)
