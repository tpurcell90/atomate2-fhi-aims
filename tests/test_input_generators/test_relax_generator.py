from fhi_aims_workflows.sets.core import RelaxSetGenerator
from ase.build import bulk, molecule

from pathlib import Path
import os
import shutil
from glob import glob
import pytest
import json

base_dir = Path(__file__).parent


def comp_system(atoms, user_params, directory):
    generator = RelaxSetGenerator(user_parameters=user_params)
    input_set = generator.get_input_set(atoms)
    input_set.write_input(directory)

    for file in glob(f"{directory}/*in"):
        assert (
            open(file, "rt").readlines()[4:]
            == open(f"ref/{file}", "rt").readlines()[4:]
        )
    assert json.load(open(f"{directory}/parameters.json")) == json.load(
        open(f"ref/{directory}/parameters.json")
    )

    shutil.rmtree(directory)


@pytest.fixture
def Si():
    return bulk("Si")


@pytest.fixture
def H2O():
    return molecule("H2O")


def test_relax_si(Si):
    parameters = {"species_dir": str(base_dir / "species_dir"), "k_grid": [2, 2, 2]}
    comp_system(Si, parameters, "relax-si/")


def test_relax_si_no_kgrid(Si):
    parameters = {"species_dir": str(base_dir / "species_dir")}
    comp_system(Si, parameters, "relax-no-kgrid-si/")


def test_relax_default_species_dir(Si):
    sd_def = os.getenv("AIMS_SPECIES_DIR", None)
    os.environ["AIMS_SPECIES_DIR"] = str(base_dir / "species_dir")
    parameters = {"k_grid": [2, 2, 2]}

    comp_system(Si, parameters, "relax-default-sd-si/")

    if sd_def:
        os.environ["AIMS_SPECIES_DIR"] = sd_def
    else:
        os.unsetenv("AIMS_SPECIES_DIR")


def test_relax_h2o(H2O):
    parameters = {"species_dir": str(base_dir / "species_dir")}
    comp_system(H2O, parameters, "relax-h2o/")


def test_relax_default_species_dir_h2o(H2O):
    sd_def = os.getenv("AIMS_SPECIES_DIR", None)
    os.environ["AIMS_SPECIES_DIR"] = str(base_dir / "species_dir")
    parameters = {"k_grid": [2, 2, 2]}

    comp_system(H2O, parameters, "relax-default-sd-h2o/")

    if sd_def:
        os.environ["AIMS_SPECIES_DIR"] = sd_def
    else:
        os.unsetenv("AIMS_SPECIES_DIR")
