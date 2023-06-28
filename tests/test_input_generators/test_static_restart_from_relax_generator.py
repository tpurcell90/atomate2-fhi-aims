from fhi_aims_workflows.sets.core import StaticSetGenerator
from ase.build import bulk, molecule

from pathlib import Path
import os
import shutil
from glob import glob
import pytest
import json

base_dir = Path(__file__).parent


def comp_system(atoms, prev_dir, directory):
    generator = StaticSetGenerator(user_parameters={})
    input_set = generator.get_input_set(
        atoms, prev_dir, properties=["energy", "forces", "stress"]
    )
    input_set.write_input(directory)

    for file in glob(f"{directory}/*in"):
        assert (
            open(file, "rt").readlines()[4:]
            == open(f"ref/{file}", "rt").readlines()[4:]
        )
    ref = json.load(open(f"ref/{directory}/parameters.json"))
    ref.pop("species_dir", None)
    check = json.load(open(f"{directory}/parameters.json"))
    check.pop("species_dir", None)

    assert ref == check
    shutil.rmtree(directory)


@pytest.fixture
def Si():
    return bulk("Si")


@pytest.fixture
def O2():
    return molecule("O2")


def test_static_from_relax_si(Si):
    comp_system(Si, f"{base_dir}/ref/relax-si/", "static-from-prev-si/")


def test_static_from_relax_si_no_kgrid(Si):
    comp_system(
        Si, f"{base_dir}/ref/relax-no-kgrid-si/", "static-from-prev-no-kgrid-si/"
    )


def test_static_from_relax_default_species_dir(Si):
    sd_def = os.getenv("AIMS_SPECIES_DIR", None)
    os.environ["AIMS_SPECIES_DIR"] = str(base_dir / "species_dir")

    comp_system(
        Si, f"{base_dir}/ref/relax-default-sd-si/", "static-from-prev-default-sd-si/"
    )

    if sd_def:
        os.environ["AIMS_SPECIES_DIR"] = sd_def
    else:
        os.unsetenv("AIMS_SPECIES_DIR")


def test_static_from_relax_o2(O2):
    comp_system(O2, f"{base_dir}/ref/relax-o2/", "static-from-prev-o2/")


def test_static_from_relax_default_species_dir_o2(O2):
    sd_def = os.getenv("AIMS_SPECIES_DIR", None)
    os.environ["AIMS_SPECIES_DIR"] = str(base_dir / "species_dir")

    comp_system(
        O2, f"{base_dir}/ref/relax-default-sd-o2/", "static-from-prev-default-sd-o2/"
    )

    if sd_def:
        os.environ["AIMS_SPECIES_DIR"] = sd_def
    else:
        os.unsetenv("AIMS_SPECIES_DIR")
