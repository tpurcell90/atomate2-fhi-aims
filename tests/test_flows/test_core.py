"""Test core FHI-aims workflows"""
import pytest

from fhi_aims_workflows.utils.MSONableAtoms import MSONableAtoms



def test_double_relax(mock_aims, Si, species_dir):
    """A test for the double relaxation flow"""
    
    from jobflow import run_locally

    from fhi_aims_workflows.flows.core import DoubleRelaxMaker
    from fhi_aims_workflows.schemas.task import AimsTaskDocument

    # mapping from job name to directory containing test files
    ref_paths = {
        "Relaxation calculation 1": "double-relax-si/relax-1",
        "Relaxation calculation 2": "double-relax-si/relax-2",
    }

    parameters = {"k_grid": [2, 2, 2], "species_dir": species_dir.as_posix()}

    # settings passed to fake_run_aims
    fake_run_kwargs = {}

    # automatically use fake AIMS
    mock_aims(ref_paths, fake_run_kwargs)

    # generate flow
    flow = DoubleRelaxMaker.from_parameters(parameters).make(MSONableAtoms(Si))

    # Run the flow or job and ensure that it finished running successfully
    responses = run_locally(flow, create_folders=True, ensure_success=True)

    # validate output
    output1 = responses[flow.jobs[0].uuid][1].output
    output2 = responses[flow.jobs[1].uuid][1].output

    assert isinstance(output1, AimsTaskDocument)
    assert output1.output.energy == pytest.approx(-15800.22554)
    assert output2.output.energy == pytest.approx(-15800.25855)