""" A test for AIMS convergence maker (used for GW, for instance)
"""

import pytest

from fhi_aims_workflows.utils.MSONableAtoms import MSONableAtoms


def test_convergence(Si, species_dir):
    """A test for the convergence job"""
    
    from jobflow import run_locally

    from fhi_aims_workflows.jobs.core import StaticMaker, StaticSetGenerator
    from fhi_aims_workflows.jobs.base import ConvergenceMaker
    from fhi_aims_workflows.schemas.task import ConvergenceSummary


    # mapping from job name to directory containing test files
    ref_paths = {
        "SCF Calculation 0": "k-grid-convergence-si/static-1",
        "SCF Calculation 1": "k-grid-convergence-si/static-2",
        "SCF Calculation 2": "k-grid-convergence-si/static-3",
    }

    input_set_parameters = {
        "species_dir": species_dir.as_posix()
    }

    parameters = {
        "maker": StaticMaker(
            input_set_generator=StaticSetGenerator(
                user_parameters=input_set_parameters
                )
            ),
        "criterion_name": "energy_per_atom",
        "epsilon": 0.2,
        "convergence_field": "k_grid",
        "convergence_steps": [[3, 3, 3],
                              [4, 4, 4],
                              [5, 5, 5],
                              [6, 6, 6]]
    }

    # settings passed to fake_run_aims
    fake_run_kwargs = {}

    # automatically use fake AIMS
    # mock_aims(ref_paths, fake_run_kwargs)

    # generate job
    job = ConvergenceMaker(**parameters).make(MSONableAtoms(Si))

    # Run the job and ensure that it finished running successfully
    responses = run_locally(job, create_folders=True, ensure_success=True)

    # a very nasty hack! 
    # but otherwise I do not know how to get the uuid of the last job in na dynamic workflow
    uuid = list(responses.keys())[-1]
    output = responses[uuid][1].output
    # validate output
    assert output.converged == True
