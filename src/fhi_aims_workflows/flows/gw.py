"""
GW workflows for FHI-aims with automatic convergence
"""
from dataclasses import dataclass, field
from pathlib import Path

from jobflow import Maker, Flow

from fhi_aims_workflows.utils.MSONableAtoms import MSONableAtoms
from fhi_aims_workflows.jobs.base import BaseAimsMaker
from fhi_aims_workflows.jobs.core import RelaxMaker, GWMaker


__all__ = ["PeriodicGWConvergenceMaker", ]


@dataclass
class PeriodicGWConvergenceMaker(Maker):
    """ A maker to perform a GW workflow with automatic convergence in FHI-aims.

    Parameters
    ----------
    name : str
        A name for the flow
    relax_maker: .RelaxMaker
        A maker that generates the relaxed structure
    gw_maker: .GWMaker
        A maker that calculates GW band gap
    """
    name: str = "GW convergence"
    relax_maker: BaseAimsMaker = field(default_factory=RelaxMaker)
    gw_maker: BaseAimsMaker = field(default_factory=GWMaker)

    def make(self, structure: MSONableAtoms, prev_dir: str | Path | None = None):
        """
        Create a flow from the relaxation and subsequent GW calculation

        Parameters
        ----------
        structure : .MSONableAtoms
            An MSON-able ASE Atoms structure object.
        prev_dir : str or Path or None
            A previous FHI-aims calculation directory to copy output files from.
        """
        relax = self.relax_maker.make(structure, prev_dir=prev_dir)
        gw = self.gw_maker.make(relax.output.structure, prev_dir=relax.output.dir_name)

        return Flow([relax, gw], gw.output, name=self.name)
