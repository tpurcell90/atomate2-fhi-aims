from fhi_aims_workflows.sets.core import StaticSetGenerator
from tests import compare_files

from pathlib import Path
import os

base_dir = Path(__file__).parent


def comp_system(atoms, prev_dir, test_name, work_path, ref_path):
    generator = StaticSetGenerator(user_parameters={})
    input_set = generator.get_input_set(
        atoms, prev_dir, properties=["energy", "forces", "stress"]
    )
    input_set.write_input(work_path / test_name)
    compare_files(test_name, work_path, ref_path)


def test_static_from_relax_si(Si, tmp_path, ref_path):
    comp_system(Si, f"{ref_path}/relax-si/", "static-from-prev-si", tmp_path, ref_path)


def test_static_from_relax_si_no_kgrid(Si, tmp_path, ref_path):
    comp_system(
        Si, f"{ref_path}/relax-no-kgrid-si/", "static-from-prev-no-kgrid-si", tmp_path, ref_path
    )


def test_static_from_relax_default_species_dir(Si, species_dir, tmp_path, ref_path):
    sd_def = os.getenv("AIMS_SPECIES_DIR", None)
    os.environ["AIMS_SPECIES_DIR"] = str(species_dir)

    comp_system(
        Si, f"{ref_path}/relax-default-sd-si/", "static-from-prev-default-sd-si", tmp_path, ref_path
    )

    if sd_def:
        os.environ["AIMS_SPECIES_DIR"] = sd_def
    else:
        os.unsetenv("AIMS_SPECIES_DIR")


def test_static_from_relax_o2(O2, tmp_path, ref_path):
    comp_system(O2, f"{ref_path}/relax-o2/", "static-from-prev-o2", tmp_path, ref_path)


def test_static_from_relax_default_species_dir_o2(O2, species_dir, tmp_path, ref_path):
    sd_def = os.getenv("AIMS_SPECIES_DIR", None)
    os.environ["AIMS_SPECIES_DIR"] = str(species_dir)

    comp_system(
        O2, f"{ref_path}/relax-default-sd-o2/", "static-from-prev-default-sd-o2", tmp_path, ref_path
    )

    if sd_def:
        os.environ["AIMS_SPECIES_DIR"] = sd_def
    else:
        os.unsetenv("AIMS_SPECIES_DIR")
