from __future__ import annotations

from dataclasses import dataclass, field
import logging
from pathlib import Path
from typing import Iterable, Sequence

from ase.atoms import Atoms
from jobflow import job, Response
from monty.serialization import dumpfn
from monty.shutil import gzip_dir
from pymatgen.core import Structure

from atomate2_temp.aims.jobs.base import BaseAimsMaker
from atomate2_temp.aims.io.parsers import read_aims_output
from atomate2_temp.aims.sets.bs import BandStructureSetGenerator, GWSetGenerator
from atomate2_temp.aims.sets.base import AimsInputGenerator
from atomate2_temp.aims.sets.core import (
    StaticSetGenerator,
    RelaxSetGenerator,
    SocketIOSetGenerator,
)
from atomate2_temp.aims.files import (
    copy_aims_outputs,
    write_aims_input_set,
    cleanup_aims_outputs,
)
from atomate2_temp.aims.utils.MSONableAtoms import MSONableAtoms
from atomate2_temp.aims.schemas.task import AimsTaskDocument
from atomate2_temp.aims.run import run_aims_socket, should_stop_children


logger = logging.getLogger(__name__)
"""Core job makers for FHI-aims workflows"""


@dataclass
class StaticMaker(BaseAimsMaker):
    """Maker to create FHI-aims SCF jobs

    Parameters
    ----------
    name : str
        The job name
    """

    calc_type: str = "scf"
    name: str = "SCF Calculation"
    input_set_generator: AimsInputGenerator = field(default_factory=StaticSetGenerator)


@dataclass
class RelaxMaker(BaseAimsMaker):
    """Maker to create relaxation calculations."""

    calc_type: str = "relax"
    input_set_generator: AimsInputGenerator = field(default_factory=RelaxSetGenerator)
    name: str = "Relaxation calculation"

    @classmethod
    def fixed_cell_relaxation(cls, *args, **kwargs):
        """Create a fixed cell relaxation maker."""
        return cls(
            input_set_generator=RelaxSetGenerator(relax_cell=False, **kwargs),
            name=cls.name + " (fixed cell)",
        )

    @classmethod
    def full_relaxation(cls, *args, **kwargs):
        """Create a full relaxation maker."""
        return cls(input_set_generator=RelaxSetGenerator(relax_cell=True, **kwargs))


@dataclass
class SocketIOStaticMaker(BaseAimsMaker):
    calc_type: str = "multi_scf"
    name: str = "SCF Calculations Socket"
    host: str = "localhost"
    port: int = 12345
    input_set_generator: AimsInputGenerator = field(
        default_factory=SocketIOSetGenerator
    )

    @job
    def make(
        self,
        atoms: Sequence[MSONableAtoms | Structure],
        prev_dir: str | Path | None = None,
    ):
        """Run an FHI-aims calculation on multiple atoms object using the socket communicator.

        Parameters
        ----------
        atoms : MSONableAtoms
            The list of atoms objects to run FHI-aims on
        prev_dir : str or Path or None
            A previous FHI-aims calculation directory to copy output files from.
        """
        # copy previous inputs

        if not isinstance(atoms, Sequence):
            atoms = [MSONableAtoms(atoms)]

        atoms = [
            at if isinstance(at, MSONableAtoms) else MSONableAtoms.from_pymatgen(at)
            for at in atoms
        ]

        from_prev = prev_dir is not None
        if from_prev:
            copy_aims_outputs(prev_dir, **self.copy_aims_kwargs)

            dest_dir = self.copy_aims_kwargs.get("dest_dir", None)
            if dest_dir is None:
                dest_dir = Path.cwd()

            images = read_aims_output(f"{dest_dir}/aims.out")
            for img in images:
                img.calc = None

            for ii in range(-1 * len(atoms), 0, -1):
                if atoms[ii] in images:
                    del atoms[ii]

        # write aims input files
        self.write_input_set_kwargs["prev_dir"] = prev_dir
        write_aims_input_set(
            atoms[0], self.input_set_generator, **self.write_input_set_kwargs
        )

        # write any additional data
        for filename, data in self.write_additional_data.items():
            dumpfn(data, filename.replace(":", "."))

        # run FHI-aims
        run_aims_socket(atoms, **self.run_aims_kwargs)

        # parse FHI-aims outputs
        task_doc = AimsTaskDocument.from_directory(
            Path.cwd(), **self.task_document_kwargs
        )
        task_doc.task_label = self.name

        # decide whether child jobs should proceed
        stop_children = should_stop_children(task_doc, **self.stop_children_kwargs)

        # cleanup files to save disk space
        cleanup_aims_outputs(directory=Path.cwd())

        # gzip folder
        # gzip_dir(".")

        return Response(
            stop_children=stop_children,
            output=task_doc if self.store_output_data else None,
        )


@dataclass
class BandStructureMaker(BaseAimsMaker):
    """A job Maker for a band structure calculation"""

    name: str = "bands"
    input_set_generator: BandStructureSetGenerator = field(
        default_factory=BandStructureSetGenerator
    )


@dataclass
class GWMaker(BaseAimsMaker):
    """A job Maker for a GW band structure calculation"""

    name: str = "GW"
    input_set_generator: GWSetGenerator = field(default_factory=GWSetGenerator)
