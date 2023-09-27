"""Test various makers"""
import os

import pytest

from fhi_aims_workflows.utils.MSONableAtoms import MSONableAtoms

cwd = os.getcwd()


def test_phonon_flow(Si, tmp_path, species_dir):

    import numpy as np

    from jobflow import run_locally

    from fhi_aims_workflows.jobs.core import StaticMaker, RelaxMaker
    from fhi_aims_workflows.schemas.task import AimsTaskDocument
    from fhi_aims_workflows.sets.core import StaticSetGenerator

    from fhi_aims_workflows.flows.phonons import PhononMaker

    # mapping from job name to directory containing test files
    # ref_paths = {"base": "static-si"}

    # settings passed to fake_run_aims; adjust these to check for certain input settings
    # fake_run_aims_kwargs = {}

    # automatically use fake FHI-aims
    # mock_aims(ref_paths, fake_run_aims_kwargs)

    parameters = {"k_grid": [2, 2, 2], "species_dir": species_dir.as_posix()}
    # generate job

    maker = PhononMaker(
        bulk_relax_maker=RelaxMaker.full_relaxation(user_parameters=parameters),
        # bulk_relax_maker=None,
        static_energy_maker=StaticMaker(
            input_set_generator=StaticSetGenerator(user_parameters=parameters)
        ),
        use_symmetrized_structure="primitive",
    )
    maker.name = "phonons"
    flow = maker.make(
        MSONableAtoms(Si),
        supercell_matrix=np.array([-1, 1, 1, 1, -1, 1, 1, 1, -1]).reshape((3, 3)),
    )

    # run the flow or job and ensure that it finished running successfully
    # os.chdir(tmp_path)
    responses = run_locally(flow, create_folders=True, ensure_success=True)
    # os.chdir(cwd)

    # validation the outputs of the job
    output = responses[flow.job_uuids[-1]][1].output
    assert output.code == "aims"
    assert output.born is None
    assert not output.has_imaginary_modes

    assert output.temperatures == list(range(0, 500, 10))
    assert output.heat_capacities[0] == 0.0
    assert np.round(output.heat_capacities[-1], 2) == 23.16
    assert (
        output.phonopy_settings.schema_json()
        == '{"title": "PhononComputationalSettings", "description": "Collection to store computational settings for the phonon computation.", "type": "object", "properties": {"npoints_band": {"title": "Npoints Band", "default": "number of points for band structure computation", "type": "integer"}, "kpath_scheme": {"title": "Kpath Scheme", "default": "indicates the kpath scheme", "type": "string"}, "kpoint_density_dos": {"title": "Kpoint Density Dos", "default": "number of points for computation of free energies and densities of states", "type": "integer"}}}'
    )
    assert np.round(output.phonon_bandstructure.bands[-1, 0], 2) == 13.99
