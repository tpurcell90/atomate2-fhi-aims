from fhi_aims_workflows.sets.ase import ASEInputGenerator

import json
import os

from pathlib import Path


def compare_files(test_name, work_dir, ref_dir):
    ref = json.load(open(f"{ref_dir / test_name}/ase_calc.json"))
    ref.pop("species_dir", None)
    check = json.load(open(f"{work_dir / test_name}/ase_calc.json"))
    check.pop("species_dir", None)

    assert ref == check


def comp_system(atoms, user_params, calc_name, test_name, work_path, ref_path):
    generator = ASEInputGenerator(user_parameters=user_params, calc_name=calc_name)
    input_set = generator.get_input_set(atoms)
    input_set.write_input(work_path / test_name)
    compare_files(test_name, work_path, ref_path)


def test_ase(Si, species_dir, tmp_path, ref_path):
    parameters = {"species_dir": str(species_dir), "k_grid": [2, 2, 2]}
    comp_system(Si, parameters, "aims", "ase-si/inputs", tmp_path, ref_path)
