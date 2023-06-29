"""A definition of base FHI-aims job Maker (closely resembling that of VASP and CP2K in atomate2)"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from jobflow import job, Maker, Response
from monty.serialization import dumpfn
from monty.shutil import gzip_dir
from pymatgen.core import Structure

from fhi_aims_workflows.files import (
    copy_aims_outputs,
    write_aims_input_set,
    cleanup_aims_outputs,
)
from fhi_aims_workflows.run import run_aims, should_stop_children
from fhi_aims_workflows.schemas.task import TaskDocument
from fhi_aims_workflows.sets.core import AimsInputGenerator
from fhi_aims_workflows.utils.MSONableAtoms import MSONableAtoms


@dataclass
class BaseAimsMaker(Maker):
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

    name: str = "base"
    input_set_generator: AimsInputGenerator = field(default_factory=AimsInputGenerator)
    write_input_set_kwargs: dict = field(default_factory=dict)
    copy_aims_kwargs: dict = field(default_factory=dict)
    run_aims_kwargs: dict = field(default_factory=dict)
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

        # copy previous inputs
        from_prev = prev_dir is not None
        if prev_dir is not None:
            copy_aims_outputs(prev_dir, **self.copy_aims_kwargs)

        # write aims input files
        self.write_input_set_kwargs["from_prev"] = from_prev
        write_aims_input_set(
            atoms, self.input_set_generator, **self.write_input_set_kwargs
        )

        # write any additional data
        for filename, data in self.write_additional_data.items():
            dumpfn(data, filename.replace(":", "."))

        # run FHI-aims
        print(Path.cwd())
        run_aims(**self.run_aims_kwargs)

        # parse FHI-aims outputs
        print(Path.cwd())
        task_doc = TaskDocument.from_directory(Path.cwd(), **self.task_document_kwargs)
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
