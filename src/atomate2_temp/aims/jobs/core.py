from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Sequence

from jobflow import Response, job
from monty.serialization import dumpfn
from pymatgen.core import Structure

from atomate2_temp.aims.files import (
    cleanup_aims_outputs,
    copy_aims_outputs,
    write_aims_input_set,
)
from atomate2_temp.aims.io.parsers import read_aims_output
from atomate2_temp.aims.jobs.base import BaseAimsMaker
from atomate2_temp.aims.run import run_aims_socket, should_stop_children
from atomate2_temp.aims.schemas.task import AimsTaskDocument
from atomate2_temp.aims.sets.base import AimsInputGenerator
from atomate2_temp.aims.sets.bs import BandStructureSetGenerator, GWSetGenerator
from atomate2_temp.aims.sets.core import (
    RelaxSetGenerator,
    SocketIOSetGenerator,
    StaticSetGenerator,
)
from atomate2_temp.aims.utils.msonable_atoms import MSONableAtoms

logger = logging.getLogger(__name__)
"""Core job makers for FHI-aims workflows"""


@dataclass
class StaticMaker(BaseAimsMaker):
    """Maker to create FHI-aims SCF jobs

    Parameters
    ----------
    calc_type: str
        The type key for the calculation
    name: str
        The job name
    input_set_generator: AimsInputGenerator
        The InputGenerator for the calculation
    """

    calc_type: str = "scf"
    name: str = "SCF Calculation"
    input_set_generator: AimsInputGenerator = field(default_factory=StaticSetGenerator)


@dataclass
class RelaxMaker(BaseAimsMaker):
    """Maker to create relaxation calculations.

    Parameters
    ----------
    calc_type: str
        The type key for the calculation
    name: str
        The job name
    input_set_generator: AimsInputGenerator
        The InputGenerator for the calculation
    """

    calc_type: str = "relax"
    name: str = "Relaxation calculation"
    input_set_generator: AimsInputGenerator = field(default_factory=RelaxSetGenerator)

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
    """Maker for the SocketIO calculator in FHI-aims

    Parameters
    ----------
    calc_type: str
        The type key for the calculation
    name: str
        The job name
    host: str
        The name of the host to maitain the socket server on
    port: int
        The port number the socket server will listen on
    input_set_generator: SocketIOSetGenerator
        The InputGenerator for the calculation
    """

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
        structure: Sequence[MSONableAtoms | Structure],
        prev_dir: str | Path | None = None,
    ) -> Response:
        """
        Run an FHI-aims calculation on multiple atoms object using the socket
        communicator.

        Parameters
        ----------
        structure : Sequence[MSONableAtoms | Structure]
            The list of atoms objects to run FHI-aims on
        prev_dir : str or Path or None
            A previous FHI-aims calculation directory to copy output files from.

        Returns
        -------
        The output response for the calculations
        """
        # copy previous inputs
        if not isinstance(structure, Sequence):
            structure = [MSONableAtoms(structure)]
        atoms = [
            st.copy()
            if isinstance(st, MSONableAtoms)
            else MSONableAtoms.from_pymatgen(st)
            for st in structure
        ]

        from_prev = prev_dir is not None
        if from_prev:
            copy_aims_outputs(prev_dir, **self.copy_aims_kwargs)

            dest_dir = self.copy_aims_kwargs.get("dest_dir", None)
            if dest_dir is None:
                dest_dir = Path.cwd()

            images = read_aims_output(f"{dest_dir}/aims.out")
            if not isinstance(images, Sequence):
                images = [images]

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

        return Response(
            stop_children=stop_children,
            output=task_doc if self.store_output_data else None,
        )


@dataclass
class BandStructureMaker(BaseAimsMaker):
    """A job Maker for a band structure calculation

    Parameters
    ----------
    calc_type: str
        The type key for the calculation
    name: str
        The job name
    input_set_generator: BandStructureSetGenerator
        The InputGenerator for the calculation
    """

    calc_type = "band_structure"
    name: str = "bands"
    input_set_generator: BandStructureSetGenerator = field(
        default_factory=BandStructureSetGenerator
    )


@dataclass
class GWMaker(BaseAimsMaker):
    """A job Maker for a GW band structure calculation

    Parameters
    ----------
    calc_type: str
        The type key for the calculation
    name: str
        The job name
    input_set_generator: GWSetGenerator
        The InputGenerator for the calculation
    """

    calc_type = "gw"
    name: str = "GW"
    input_set_generator: GWSetGenerator = field(default_factory=GWSetGenerator)
