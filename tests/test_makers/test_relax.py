from pathlib import Path

import pytest

from fhi_aims_workflows.utils.MSONableAtoms import MSONableAtoms
from ase.build import bulk


@pytest.fixture
def Si():
    return bulk("Si")


# def test_base_maker(tmp_path, mock_aims, Si):
def test_relax_full_maker(Si):
    import os

    from jobflow import run_locally

    from fhi_aims_workflows.jobs.core import RelaxMaker
    from fhi_aims_workflows.schemas.task import TaskDocument

    # mapping from job name to directory containing test files
    ref_paths = {"base": "relax_Si"}

    # settings passed to fake_run_aims; adjust these to check for certain input settings
    fake_run_aims_kwargs = {}

    # automatically use fake FHI-aims
    # mock_aims(ref_paths, fake_run_aims_kwargs)

    parameters = {"species_dir": (Path(__file__).parents[1] / "species_dir").as_posix()}
    # generate job
    maker = RelaxMaker.full_relaxation(user_parameters=parameters)
    job = maker.make(MSONableAtoms(Si))

    # run the flow or job and ensure that it finished running successfully
    os.chdir(tmp_path)
    responses = run_locally(job, create_folders=True, ensure_success=True)

    # validation the outputs of the job
    output1 = responses[job.uuid][1].output
    assert isinstance(output1, TaskDocument)
    # assert output1.output.energy == pytest.approx(-15800.099740991)


def test_relax_fixed_cell_maker(tmp_path, Si):
    import os

    from jobflow import run_locally

    from fhi_aims_workflows.jobs.core import RelaxMaker
    from fhi_aims_workflows.schemas.task import TaskDocument
    from fhi_aims_workflows.sets.core import RelaxSetGenerator

    # mapping from job name to directory containing test files
    ref_paths = {"base": "relax_fixed_cell_Si"}

    # settings passed to fake_run_aims; adjust these to check for certain input settings
    fake_run_aims_kwargs = {}

    # automatically use fake FHI-aims
    # mock_aims(ref_paths, fake_run_aims_kwargs)

    parameters = {"species_dir": (Path(__file__).parents[1] / "species_dir").as_posix()}
    # generate job
    maker = RelaxMaker.fixed_cell_relaxation(user_parameters=parameters)
    job = maker.make(MSONableAtoms(Si))

    # run the flow or job and ensure that it finished running successfully
    os.chdir(tmp_path)
    responses = run_locally(job, create_folders=True, ensure_success=True)

    # validation the outputs of the job
    output1 = responses[job.uuid][1].output
    assert isinstance(output1, TaskDocument)
    # assert output1.output.energy == pytest.approx(-15800.099740991)
