"""
GW workflows for FHI-aims with automatic convergence
"""
from copy import deepcopy
from dataclasses import dataclass, field
from pathlib import Path

from jobflow import Flow
from pymatgen.core import Molecule, Structure

from atomate2_temp.aims.jobs.base import BaseAimsMaker, ConvergenceMaker
from atomate2_temp.aims.jobs.core import BandStructureMaker, GWMaker, StaticMaker
from atomate2_temp.aims.sets.bs import BandStructureSetGenerator, GWSetGenerator
from atomate2_temp.aims.sets.core import StaticSetGenerator
from atomate2_temp.aims.utils.msonable_atoms import MSONableAtoms

__all__ = [
    "PeriodicGWConvergenceMaker",
]


@dataclass
class PeriodicGWConvergenceMaker(BaseAimsMaker):
    """
    A maker to perform a GW workflow with automatic convergence in FHI-aims.

    Parameters
    ----------
    name : str
        A name for the job
    criterion_name: str
        A name for the convergence criterion. Must be in the run results
    epsilon: float
        A difference in criterion value for subsequent runs
    convergence_field: str
        An input parameter that changes to achieve convergence
    convergence_steps: list | tuple
        An iterable of the possible values for the convergence field.
        If the iterable is depleted and the convergence is not reached,
        that the job is failed
    """

    name: str = "GW convergence"
    criterion_name: str = "bandgap"
    epsilon: float = 0.001
    convergence_field: str = field(default_factory=str)
    convergence_steps: list = field(default_factory=list)

    def make(
        self,
        structure: MSONableAtoms | Structure | Molecule,
        prev_dir: str | Path | None = None,
    ) -> Flow:
        """
        Create a flow from the DFT ground state and subsequent GW calculation.

        Parameters
        ----------
        structure : .MSONableAtoms, Structure, or Molecule
            The strcuture to calculate
        prev_dir : str or Path or None
            A previous FHI-aims calculation directory to copy output files from.
        """

        parameters = self.input_set_generator.user_parameters
        parameters["elsi_restart"] = ["read_and_write", 1]
        # the first calculation
        if all(structure.pbc):
            input_set = BandStructureSetGenerator(user_parameters=deepcopy(parameters))
            static_maker = BandStructureMaker(
                input_set_generator=input_set, run_aims_kwargs=self.run_aims_kwargs
            )
        else:
            input_set = StaticSetGenerator(user_parameters=deepcopy(parameters))
            static_maker = StaticMaker(
                input_set_generator=input_set, run_aims_kwargs=self.run_aims_kwargs
            )

        static = static_maker.make(structure, prev_dir=prev_dir)

        gw_input_set = GWSetGenerator(user_parameters=parameters)
        gw_maker = GWMaker(
            input_set_generator=gw_input_set, run_aims_kwargs=self.run_aims_kwargs
        )
        convergence = ConvergenceMaker(
            maker=gw_maker,
            epsilon=self.epsilon,
            criterion_name=self.criterion_name,
            convergence_field=self.convergence_field,
            convergence_steps=self.convergence_steps,
        )
        gw = convergence.make(static.output.structure, prev_dir=static.output.dir_name)
        return Flow([static, gw], gw.output, name=self.name)
