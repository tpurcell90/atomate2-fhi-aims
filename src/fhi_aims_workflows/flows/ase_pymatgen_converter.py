from jobflow import Flow, Maker, job
from dataclasses import dataclass, field

from pymatgen.core.structure import Structure, Molecule

from fhi_aims_workflows.jobs.ase_pymatgen_conversion import (
    convert_to_structure,
    convert_mult_to_structure,
    convert_to_atoms,
)

from fhi_aims_workflows.jobs.core import (
    StaticMaker,
    SocketIOStaticMaker,
)
from fhi_aims_workflows.jobs.base import BaseAimsMaker
from typing import Iterable


@dataclass
class ASECalculationMaker(BaseAimsMaker):
    name: str = "ASE Calculation"
    static_maker: BaseAimsMaker = field(default_factory=StaticMaker)
    socket_maker: BaseAimsMaker = field(default_factory=SocketIOStaticMaker)

    def make(
        self,
        structure: Structure | Iterable[Structure],
        use_socket: bool = False,
    ):
        self.static_maker.name = f"{self.name}_{self.static_maker.name}"
        self.socket_maker.name = f"{self.name}_{self.socket_maker.name}"
        if isinstance(structure, Structure) or isinstance(structure, Molecule):
            use_socket = False
            structure = [structure]
        elif isinstance(structure, Iterable) and len(structure) == 1:
            use_socket = False

        convert_jobs = [convert_to_atoms(struct) for struct in structure]

        calc_name = "aims"
        if use_socket:
            calc_jobs = [
                self.socket_maker.make(
                    atoms=[job.output for job in convert_jobs],
                )
            ]
            traj = calc_jobs[0].output.output.trajectory
            reconvert_jobs = [
                convert_mult_to_structure(
                    calc_jobs[0].output.output.trajectory,
                )
            ]
        else:
            calc_jobs = [self.static_maker.make(job.output) for job in convert_jobs]
            reconvert_jobs = [
                convert_to_structure(
                    job.output.structure,
                )
                for job in calc_jobs
            ]

        return Flow(calc_jobs + convert_jobs + reconvert_jobs, name=self.name)
