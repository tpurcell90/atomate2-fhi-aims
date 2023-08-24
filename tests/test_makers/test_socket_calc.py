from pathlib import Path

import pytest

from fhi_aims_workflows.utils.MSONableAtoms import MSONableAtoms
from ase.build import bulk
import os


cwd = os.getcwd()


def test_static_socket_maker(Si, species_dir, mock_aims, tmp_path):
    from jobflow import run_locally

    from fhi_aims_workflows.jobs.core import SocketIOStaticMaker
    from fhi_aims_workflows.schemas.task import TaskDocument
    from fhi_aims_workflows.sets.core import SocketIOSetGenerator
    from fhi_aims_workflows.io.parsers import read_aims_output

    atoms = MSONableAtoms(Si)
    atoms_list = [atoms, atoms.copy(), atoms.copy()]
    atoms_list[1].positions[0, 0] += 0.02
    atoms_list[2].cell[:, :] *= 1.02

    # mapping from job name to directory containing test files
    ref_paths = {"socket": "socket_tests"}

    # settings passed to fake_run_aims; adjust these to check for certain input settings
    fake_run_aims_kwargs = {}

    # automatically use fake FHI-aims
    mock_aims(ref_paths, fake_run_aims_kwargs)

    parameters = {
        "k_grid": [2, 2, 2],
        "species_dir": species_dir.as_posix(),
    }
    # generate job
    maker = SocketIOStaticMaker(
        input_set_generator=SocketIOSetGenerator(user_parameters=parameters)
    )
    maker.name = "socket"
    job = maker.make(atoms_list)

    # run the flow or job and ensure that it finished running successfully
    # os.chdir(tmp_path)
    responses = run_locally(job, create_folders=True, ensure_success=True)
    # os.chdir(cwd)

    # validation the outputs of the job
    outputs = responses[job.uuid][1].output
    assert isinstance(outputs, TaskDocument)
    assert len(outputs.output.trajectory) == 3
    assert outputs.output.trajectory[0].get_potential_energy() == pytest.approx(
        -15800.0997410132
    )
    assert outputs.output.trajectory[1].get_potential_energy() == pytest.approx(
        -15800.0962356206
    )
    assert outputs.output.trajectory[2].get_potential_energy() == pytest.approx(
        -15800.1847237514
    )


def test_ase_socket_maker(Si, species_dir, mock_aims, tmp_path):
    from jobflow import run_locally
    from pymatgen.io.ase import AseAtomsAdaptor

    from fhi_aims_workflows.flows.ase_pymatgen_converter import ASECalculationMaker
    from fhi_aims_workflows.jobs.core import SocketIOStaticMaker
    from fhi_aims_workflows.schemas.task import TaskDocument
    from fhi_aims_workflows.sets.core import SocketIOSetGenerator
    from fhi_aims_workflows.io.parsers import read_aims_output

    ase_adaptor = AseAtomsAdaptor()

    atoms = MSONableAtoms(Si)
    atoms_list = [atoms, atoms.copy(), atoms.copy()]
    atoms_list[1].positions[0, 0] += 0.02
    atoms_list[2].cell[:, :] *= 1.02

    structures = [ase_adaptor.get_structure(at) for at in atoms_list]

    # mapping from job name to directory containing test files
    ref_paths = {"socket": "socket_tests"}

    # settings passed to fake_run_aims; adjust these to check for certain input settings
    fake_run_aims_kwargs = {}

    # automatically use fake FHI-aims
    mock_aims(ref_paths, fake_run_aims_kwargs)

    parameters = {
        "k_grid": [2, 2, 2],
        "species_dir": species_dir.as_posix(),
    }
    # generate job
    maker = ASECalculationMaker(
        socket_maker=SocketIOStaticMaker(
            input_set_generator=SocketIOSetGenerator(user_parameters=parameters),
            port=31415,
        )
    )
    maker.name = "ase_socket"
    flow = maker.make(structures, True)

    # run the flow or job and ensure that it finished running successfully
    # os.chdir(tmp_path)
    responses = run_locally(flow, create_folders=True, ensure_success=True)
    # os.chdir(cwd)

    # validation the outputs of the job
    outputs = responses[flow.jobs[-1].uuid][1].output
    assert isinstance(outputs, TaskDocument)
    assert len(outputs.output.trajectory) == 3
    assert outputs.output.trajectory[0].get_potential_energy() == pytest.approx(
        -15800.0997410132
    )
    assert outputs.output.trajectory[1].get_potential_energy() == pytest.approx(
        -15800.0962356206
    )
    assert outputs.output.trajectory[2].get_potential_energy() == pytest.approx(
        -15800.1847237514
    )
