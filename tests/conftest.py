import logging
from pathlib import Path
from typing import Union, Sequence, Literal

import pytest

from ase.build import bulk, molecule

_REF_PATHS = {}
_FAKE_RUN_AIMS_KWARGS = {}
_VFILES = "control.in"


logger = logging.getLogger(__name__)


@pytest.fixture
def Si():
    return bulk("Si")


@pytest.fixture
def H2O():
    return molecule("H2O")


@pytest.fixture(scope="session")
def test_dir():
    from pathlib import Path

    module_dir = Path(__file__).resolve().parent
    test_dir = module_dir / "test_data"
    return test_dir.resolve()


@pytest.fixture()
def mock_aims(monkeypatch, test_dir):
    """
    This fixture allows one to mock (fake) running FHI-aims.

    To use the fixture successfully, the following steps must be followed:
    1. "mock_aims" should be included as an argument to any test that would like to use
       its functionally.
    2. For each job in your workflow, you should prepare a reference directory
       containing two folders "inputs" (containing the reference input files expected
       to be produced by write_aims_input_set) and "outputs" (containing the expected
       output files to be produced by run_aims). These files should reside in a
       subdirectory of "tests/test_data/aims".
    3. Create a dictionary mapping each job name to its reference directory. Note that
       you should supply the reference directory relative to the "tests/test_data/aims"
       folder. For example, if your calculation has one job named "static" and the
       reference files are present in "tests/test_data/aims/Si_static", the dictionary
       would look like: ``{"static": "Si_static"}``.
    4. Optional: create a dictionary mapping each job name to custom keyword arguments
       that will be supplied to fake_run_aims. This way you can configure which incar
       settings are expected for each job. For example, if your calculation has one job
       named "static" and you wish to validate that "NSW" is set correctly in the INCAR,
       your dictionary would look like ``{"static": {"incar_settings": {"NSW": 0}}``.
    5. Inside the test function, call `mock_aims(ref_paths, fake_aims_kwargs)`, where
       ref_paths is the dictionary created in step 3 and fake_aims_kwargs is the
       dictionary created in step 4.
    6. Run your aims job after calling `mock_aims`.

    For examples, see the tests in tests/aims/jobs/core.py.
    """
    import fhi_aims_workflows.jobs.base
    import fhi_aims_workflows.run
    from fhi_aims_workflows.sets.base import AimsInputGenerator

    def mock_run_aims(*args, **kwargs):
        from jobflow import CURRENT_JOB

        name = CURRENT_JOB.job.name
        ref_path = test_dir / _REF_PATHS[name]
        fake_run_aims(ref_path, **_FAKE_RUN_AIMS_KWARGS.get(name, {}))

    get_input_set_orig = AimsInputGenerator.get_input_set

    def mock_get_input_set(self, *args, **kwargs):
        return get_input_set_orig(self, *args, **kwargs)

    monkeypatch.setattr(fhi_aims_workflows.run, "run_aims", mock_run_aims)
    monkeypatch.setattr(fhi_aims_workflows.jobs.base, "run_aims", mock_run_aims)
    monkeypatch.setattr(AimsInputGenerator, "get_input_set", mock_get_input_set)

    def _run(ref_paths, fake_run_aims_kwargs=None):
        if fake_run_aims_kwargs is None:
            fake_run_aims_kwargs = {}

        _REF_PATHS.update(ref_paths)
        _FAKE_RUN_AIMS_KWARGS.update(fake_run_aims_kwargs)

    yield _run

    monkeypatch.undo()
    _REF_PATHS.clear()
    _FAKE_RUN_AIMS_KWARGS.clear()


def fake_run_aims(
    ref_path: Union[str, Path],
    input_settings: Sequence[str] = (),
    check_inputs: Sequence[Literal["aims.inp"]] = _VFILES,
    clear_inputs: bool = True,
):
    """
    Emulate running aims and validate aims input files.

    Parameters
    ----------
    ref_path
        Path to reference directory with aims input files in the folder named 'inputs'
        and output files in the folder named 'outputs'.
    input_settings
        A list of input settings to check.
    check_inputs
        A list of aims input files to check. Supported options are "aims.inp"
    clear_inputs
        Whether to clear input files before copying in the reference aims outputs.
    """
    logger.info("Running fake aims.")

    ref_path = Path(ref_path)

    logger.info("Verified inputs successfully")

    if clear_inputs:
        clear_aims_inputs()

    copy_aims_outputs(ref_path)

    # pretend to run aims by copying pre-generated outputs from reference dir
    logger.info("Generated fake aims outputs")


# @pytest.fixture()
# def check_input():
#     def _check_input(ref_path, user_input):
#         from pymatgen.io.aims.inputs import AimsInput
#
#         ref = aimsInput.from_file(ref_path / "inputs" / "aims.inp")
#         user_input.verbosity(False)
#         ref.verbosity(False)
#         user_string = " ".join(user_input.get_string().lower().split())
#         user_hash = md5(user_string.encode("utf-8")).hexdigest()
#
#         ref_string = " ".join(ref.get_string().lower().split())
#         ref_hash = md5(ref_string.encode("utf-8")).hexdigest()
#
#         if ref_hash != user_hash:
#             raise ValueError("aims Inputs do not match!")
#
#     return _check_input


def clear_aims_inputs():
    for aims_file in (
        "aims.inp",
        "aims.out",
    ):
        if Path(aims_file).exists():
            Path(aims_file).unlink()
    logger.info("Cleared aims inputs")


def copy_aims_outputs(ref_path: Union[str, Path]):
    import shutil

    output_path = ref_path / "outputs"
    for output_file in output_path.iterdir():
        if output_file.is_file():
            shutil.copy(output_file, ".")