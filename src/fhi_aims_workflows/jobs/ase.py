from jobflow import job, Response
from dataclasses import dataclass, field

from pathlib import Path


from fhi_aims_workflows.sets.ase import ASEInputGenerator
from fhi_aims_workflows.utils.MSONableAtoms import MSONableAtoms

import logging
from fhi_aims_workflows.schemas.ase import TaskDocument
from fhi_aims_workflows.run import run_ase, run_ase_socket
from monty.shutil import gzip_dir

from typing import Iterable

logger = logging.getLogger(__name__)
"""Core job makers for FHI-aims workflows"""

from dataclasses import dataclass, field


@dataclass
class BaseASEMaker(Maker):
    """
    Base FHI-aims job maker.

    Parameters
    ----------
    name : str
        The job name.
    input_set_generator : AimsInputGenerator
        A generator used to make the input set.
    write_input_set_kwargs : dict
        Keyword arguments that will get passed to :obj:`.write_aims_input_set`.
    copy_aims_kwargs : dict
        Keyword arguments that will get passed to :obj:`.copy_aims_outputs`.
    run_aims_kwargs : dict
        Keyword arguments that will get passed to :obj:`.run_aims`.
    task_document_kwargs : dict
        Keyword arguments that will get passed to :obj:`.TaskDocument.from_directory`.
    stop_children_kwargs : dict
        Keyword arguments that will get passed to :obj:`.should_stop_children`.
    write_additional_data : dict
        Additional data to write to the current directory. Given as a dict of
        {filename: data}. Note that if using FireWorks, dictionary keys cannot contain
        the "." character which is typically used to denote file extensions. To avoid
        this, use the ":" character, which will automatically be converted to ".". E.g.
        ``{"my_file:txt": "contents of the file"}``.
    store_output_data: bool
        Whether the job output (TaskDocument) should be stored in the JobStore through
        the response.
    """

    name: str = "ase_base"
    input_set_generator: ASEInputGenerator = field(default_factory=ASEInputGenerator)
    run_ase_kwargs: dict = field(default_factory=dict)
    task_document_kwargs: dict = field(default_factory=dict)
    stop_children_kwargs: dict = field(default_factory=dict)
    write_additional_data: dict = field(default_factory=dict)
    store_output_data: bool = True

    @job
    def make(self, atoms: MSONableAtoms, prev_dir: str | Path | None = None):
        """
        Run an FHI-aims calculation.

        Parameters
        ----------
        atoms : MSONableAtoms
            An ASE Atoms or pymatgen Structure object.
        prev_dir : str or Path or None
            A previous FHI-aims calculation directory to copy output files from.
        """
        # the structure transformation part was deleted; can be reinserted when needed

        # Create Input Set
        input_set = input_set_generator.get_input_set(atoms, prev_dir)

        # run FHI-aims
        ran_atoms = run_ase(
            input_set.atoms,
            input_set.calc_name,
            input_set.calc_parameters,
            input_set.properties,
        )

        # parse FHI-aims outputs
        print(Path.cwd())
        task_doc = TaskDocument.from_atoms(atoms)
        task_doc.task_label = self.name

        # decide whether child jobs should proceed
        stop_children = should_stop_children(task_doc, **self.stop_children_kwargs)

        # cleanup files to save disk space
        cleanup_aims_outputs(directory=Path.cwd())

        # gzip folder
        gzip_dir(".")

        return Response(
            stop_children=stop_children,
            # stored_data={"custodian": task_doc.custodian},
            output=task_doc if self.store_output_data else None,
        )
