"""A definition of base FHI-aims job Maker (closely resembling that of VASP and CP2K in atomate2)"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Type

from jobflow import job, Maker, Response, Flow
from monty.serialization import dumpfn
from monty.shutil import gzip_dir

from fhi_aims_workflows.files import (
    copy_aims_outputs,
    write_aims_input_set,
    cleanup_aims_outputs,
)
from fhi_aims_workflows.run import run_aims, should_stop_children
from fhi_aims_workflows.schemas.task import AimsTaskDocument
from fhi_aims_workflows.sets.base import AimsInputGenerator
from fhi_aims_workflows.utils.MSONableAtoms import MSONableAtoms


logger = logging.getLogger(__name__)
CONVERGENCE_FILE_NAME = 'convergence.json'  # make it a constant?


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
        if prev_dir is not None:
            copy_aims_outputs(prev_dir, **self.copy_aims_kwargs)

        # write aims input files
        self.write_input_set_kwargs["prev_dir"] = prev_dir
        write_aims_input_set(
            atoms, self.input_set_generator, **self.write_input_set_kwargs
        )

        # write any additional data
        for filename, data in self.write_additional_data.items():
            dumpfn(data, filename.replace(":", "."))

        # run FHI-aims
        run_aims(**self.run_aims_kwargs)

        # parse FHI-aims outputs
        task_doc = AimsTaskDocument.from_directory(Path.cwd(), **self.task_document_kwargs)
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
class ConvergenceJob(Maker):
    """ A job that performs convergence run for a given number of steps

    Parameters
    ----------
    name : str
        A name for the job
    maker: .BaseAimsMaker
        A maker for the run
    criterion_name: str
        A name for the convergence criterion. Must be in the run results
    epsilon: float
        A difference in criterion value for subsequent runs
    convergence_field: str
        An input parameter that changes to achieve convergence
    convergence_steps: list | tuple
        An iterable of the possible values for the convergence field. If the iterable is depleted and the
        convergence is not reached, that the job is failed
    """
    name: str = "Convergence job"
    maker: BaseAimsMaker = field(default_factory=BaseAimsMaker)
    criterion_name: str = "energy_per_atom"
    epsilon: float = 0.001
    convergence_field: str = field(default_factory=str)
    convergence_steps: list = field(default_factory=list)

    def __post_init__(self):
        self.last_idx = len(self.convergence_steps)

    @job
    def make(self, atoms,
             prev_dir: str | Path = None,
             criterion_value: float = None):
        # getting the calculation index
        idx = 0
        converged = False
        if prev_dir is not None:
            prev_dir = prev_dir.split(':')[-1]
            convergence_file = Path(prev_dir) / CONVERGENCE_FILE_NAME
            with open(convergence_file) as f:
                data = json.load(f)
                # check for convergence
                if len(data['criterion_values']) > 1:
                    converged = abs(data['criterion_values'][-1] - data['criterion_values'][-2]) < self.epsilon
                idx = data['idx'] + 1

        if idx < self.last_idx and not converged:
            # finding next jobs
            next_base_job = self.maker.make(atoms, prev_dir=prev_dir)
            next_base_job.update_maker_kwargs(
                {"_set": {f"input_set_generator->user_parameters->"
                          f"{self.convergence_field}": self.convergence_steps[idx]}},
                dict_mod=True
            )
            update_file_job = self.update_convergence_file(prev_dir=prev_dir,
                                                           job_dir=next_base_job.output.dir_name,
                                                           output=next_base_job.output)

            next_job = self.make(atoms,
                                 prev_dir=next_base_job.output.dir_name)

            replace_flow = Flow([next_base_job,
                                 update_file_job,
                                 next_job], output=next_base_job.output)
        else:
            get_results_job = self.get_results(prev_dir=prev_dir)
            replace_flow = Flow([get_results_job], output=get_results_job.output)
        return Response(addition=replace_flow)

    @job(name='Writing a convergence file')
    def update_convergence_file(self, prev_dir, job_dir, output):
        idx = 0
        if prev_dir is not None:
            prev_dir = prev_dir.split(':')[-1]
            convergence_file = Path(prev_dir) / CONVERGENCE_FILE_NAME
            with open(convergence_file) as f:
                convergence_data = json.load(f)
                idx = convergence_data['idx'] + 1
        else:
            convergence_data = {
                'criterion_name': self.criterion_name,
                'criterion_values': [],
                'convergence_field_name': self.convergence_field,
                'convergence_field_values': [],
                'idx': 0
            }
        convergence_data['convergence_field_values'].append(self.convergence_steps[idx])
        convergence_data['criterion_values'].append(getattr(output.output, self.criterion_name))
        convergence_data['idx'] = idx

        job_dir = job_dir.split(':')[-1]
        convergence_file = Path(job_dir) / CONVERGENCE_FILE_NAME
        with open(convergence_file, 'w') as f:
            json.dump(convergence_data, f)

    @job(name='Getting the results')
    def get_results(self, prev_dir):
        convergence_file = Path(prev_dir) / CONVERGENCE_FILE_NAME
        with open(convergence_file) as f:
            return json.load(f)

