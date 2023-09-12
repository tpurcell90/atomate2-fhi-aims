"""
GW workflows for FHI-aims with automatic convergence
"""
from dataclasses import dataclass, field
from pathlib import Path

from jobflow import Maker, Flow

from fhi_aims_workflows.utils.MSONableAtoms import MSONableAtoms
from fhi_aims_workflows.jobs.base import BaseAimsMaker, ConvergenceMaker
from fhi_aims_workflows.jobs.core import StaticMaker

__all__ = ["PeriodicGWConvergenceMaker", ]


@dataclass
class PeriodicGWConvergenceMaker(Maker):
    """ A maker to perform a GW workflow with automatic convergence in FHI-aims.

    Parameters
    ----------
    name : str
        A name for the flow
    static_maker: .StaticMaker
        A maker that generates the static point calculation
    gw_maker: .ConvergenceMaker
        A maker that checks the convergence for GW band gap calculations
    """
    name: str = "GW convergence"
    static_maker: BaseAimsMaker = field(default_factory=StaticMaker)
    convergence_maker: ConvergenceMaker = field(default_factory=ConvergenceMaker)

    def make(self, structure: MSONableAtoms, prev_dir: str | Path | None = None):
        """
        Create a flow from the DFT ground state and subsequent GW calculation

        Parameters
        ----------
        structure : .MSONableAtoms
            An MSON-able ASE Atoms structure object.
        prev_dir : str or Path or None
            A previous FHI-aims calculation directory to copy output files from.
        """
        static = self.static_maker.make(structure, prev_dir=prev_dir)
        gw = self.convergence_maker.make(static.output.structure, prev_dir=static.output.dir_name)

        return Flow([static, gw], gw.output, name=self.name)
