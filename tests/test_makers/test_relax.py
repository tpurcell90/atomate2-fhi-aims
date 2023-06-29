from pathlib import Path

import pytest

from fhi_aims_workflows.utils.MSONableAtoms import MSONableAtoms
from ase.build import bulk
import os

from jobflow import run_locally

from fhi_aims_workflows.jobs.core import RelaxMaker
from fhi_aims_workflows.schemas.task import TaskDocument


def test_base_maker(tmp_path, species_dir, mock_aims, Si):
    # mapping from job name to directory containing test files
    ref_paths = {"relax_si": "relax_si"}

    # settings passed to fake_run_aims; adjust these to check for certain input settings
    fake_run_aims_kwargs = {}

    # automatically use fake FHI-aims
    mock_aims(ref_paths, fake_run_aims_kwargs)

    parameters = {"k_grid": [2, 2, 2], "species_dir": species_dir.as_posix()}
    # generate job
    maker = RelaxMaker.full_relaxation(user_parameters=parameters)
    maker.name = "relax_si"
    job = maker.make(MSONableAtoms(Si))

    # run the flow or job and ensure that it finished running successfully
    os.chdir(tmp_path)
    responses = run_locally(job, create_folders=True, ensure_success=True)

    # validation the outputs of the job
    output1 = responses[job.uuid][1].output
    assert isinstance(output1, TaskDocument)
    assert output1.output.energy == pytest.approx(-15800.2255448846)


def test_relax_fixed_cell_maker(tmp_path, species_dir, mock_aims, Si):
    # mapping from job name to directory containing test files
    ref_paths = {"relax_fixed_cell_si": "relax_fixed_cell_si"}

    # settings passed to fake_run_aims; adjust these to check for certain input settings
    fake_run_aims_kwargs = {}

    # automatically use fake FHI-aims
    mock_aims(ref_paths, fake_run_aims_kwargs)

    parameters = {"k_grid": [2, 2, 2], "species_dir": species_dir.as_posix()}
    # generate job
    maker = RelaxMaker.fixed_cell_relaxation(user_parameters=parameters)
    maker.name = "relax_fixed_cell_si"
    atoms = Si.copy()
    atoms.positions[0, 0] += 0.25
    job = maker.make(MSONableAtoms(atoms))

    # run the flow or job and ensure that it finished running successfully
    os.chdir(tmp_path)
    responses = run_locally(job, create_folders=True, ensure_success=True)

    # validation the outputs of the job
    output1 = responses[job.uuid][1].output
    assert isinstance(output1, TaskDocument)
    assert output1.output.energy == pytest.approx(-15800.099741042)
