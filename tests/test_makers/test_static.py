"""Test various makers"""
import os

import pytest

from fhi_aims_workflows.schemas.calculation import AimsObject
from fhi_aims_workflows.utils.MSONableAtoms import MSONableAtoms
from ase.build import bulk

cwd = os.getcwd()


def test_static_maker(Si, tmp_path, mock_aims, species_dir):
    from jobflow import run_locally

    from fhi_aims_workflows.jobs.core import StaticMaker
    from fhi_aims_workflows.schemas.task import TaskDocument
    from fhi_aims_workflows.sets.core import StaticSetGenerator

    # mapping from job name to directory containing test files
    ref_paths = {"base": "static-si"}

    # settings passed to fake_run_aims; adjust these to check for certain input settings
    fake_run_aims_kwargs = {}

    # automatically use fake FHI-aims
    mock_aims(ref_paths, fake_run_aims_kwargs)

    parameters = {"k_grid": [2, 2, 2], "species_dir": species_dir.as_posix()}
    # generate job
    maker = StaticMaker(
        input_set_generator=StaticSetGenerator(user_parameters=parameters)
    )
    maker.name = "base"
    job = maker.make(MSONableAtoms(Si))

    # run the flow or job and ensure that it finished running successfully
    os.chdir(tmp_path)
    responses = run_locally(job, create_folders=True, ensure_success=True)
    os.chdir(cwd)

    # validation the outputs of the job
    output1 = responses[job.uuid][1].output
    assert isinstance(output1, TaskDocument)
    assert output1.output.energy == pytest.approx(-15800.099740991)


def test_ase_static_maker(Si, tmp_path, mock_aims, species_dir):
    from jobflow import run_locally
    from pymatgen.io.ase import AseAtomsAdaptor

    from fhi_aims_workflows.flows.ase_pymatgen_converter import ASECalculationMaker
    from fhi_aims_workflows.jobs.core import StaticMaker
    from fhi_aims_workflows.schemas.task import TaskDocument
    from fhi_aims_workflows.schemas.ase import ASEOutput
    from fhi_aims_workflows.sets.core import StaticSetGenerator

    ase_adaptor = AseAtomsAdaptor()
    structure = AseAtomsAdaptor.get_structure(Si)

    # mapping from job name to directory containing test files
    ref_paths = {"base_SCF Calculation": "static-si"}

    # settings passed to fake_run_aims; adjust these to check for certain input settings
    fake_run_aims_kwargs = {}

    # automatically use fake FHI-aims
    mock_aims(ref_paths, fake_run_aims_kwargs)

    parameters = {"k_grid": [2, 2, 2], "species_dir": species_dir.as_posix()}
    # generate job
    maker = ASECalculationMaker(
        static_maker=StaticMaker(
            input_set_generator=StaticSetGenerator(user_parameters=parameters)
        )
    )
    maker.name = "base"
    flow = maker.make(structure)

    # run the flow or job and ensure that it finished running successfully
    os.chdir(tmp_path)
    responses = run_locally(flow, create_folders=True, ensure_success=True)
    os.chdir(cwd)

    # validation the outputs of the job
    output1 = responses[flow.jobs[0].uuid][1].output
    assert isinstance(output1, TaskDocument)
    assert output1.output.energy == pytest.approx(-15800.099740991)

    output_reconvert = responses[flow.jobs[1].uuid][1].output
    assert isinstance(output_reconvert, ASEOutput)
    assert output_reconvert.energy == pytest.approx(-15800.099740991)
