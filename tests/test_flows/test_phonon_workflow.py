"""Test various makers"""
import os

from atomate2_temp.aims.utils.msonable_atoms import MSONableAtoms

cwd = os.getcwd()


def test_phonon_flow(Si, tmp_path, mock_aims, species_dir):
    import numpy as np

    from jobflow import run_locally

    from atomate2_temp.aims.jobs.core import StaticMaker, RelaxMaker
    from atomate2_temp.aims.jobs.phonons import PhononDisplacementMaker

    from atomate2_temp.aims.sets.core import StaticSetGenerator

    from atomate2_temp.aims.flows.phonons import PhononMaker

    # mapping from job name to directory containing test files
    ref_paths = {
        "Relaxation calculation": "phonon-relax-si",
        "phonon static aims 1/1": "phonon-disp-si",
        "SCF Calculation": "phonon-energy-si",
    }

    # settings passed to fake_run_aims; adjust these to check for certain input settings
    fake_run_aims_kwargs = {}

    # automatically use fake FHI-aims
    mock_aims(ref_paths, fake_run_aims_kwargs)

    parameters = {"k_grid": [2, 2, 2], "species_dir": species_dir.as_posix()}
    # generate job

    parameters_phonon_disp = dict(compute_forces=True, **parameters)
    maker = PhononMaker(
        bulk_relax_maker=RelaxMaker.full_relaxation(user_parameters=parameters),
        static_energy_maker=StaticMaker(
            input_set_generator=StaticSetGenerator(user_parameters=parameters)
        ),
        use_symmetrized_structure="primitive",
        phonon_displacement_maker=PhononDisplacementMaker(
            input_set_generator=StaticSetGenerator(
                user_parameters=parameters_phonon_disp,
                user_kpoints_settings={"density": 5.0, "even": True},
            )
        ),
    )
    maker.name = "phonons"
    flow = maker.make(
        MSONableAtoms(Si),
        supercell_matrix=np.array([-1, 1, 1, 1, -1, 1, 1, 1, -1]).reshape((3, 3)),
    )

    # run the flow or job and ensure that it finished running successfully
    os.chdir(tmp_path)
    responses = run_locally(flow, create_folders=True, ensure_success=True)
    os.chdir(cwd)

    # validation the outputs of the job
    output = responses[flow.job_uuids[-1]][1].output
    assert output.code == "aims"
    assert output.born is None
    assert not output.has_imaginary_modes

    assert output.temperatures == list(range(0, 500, 10))
    assert output.heat_capacities[0] == 0.0
    assert np.round(output.heat_capacities[-1], 2) == 23.06
    assert (
        output.phonopy_settings.schema_json()
        == '{"title": "PhononComputationalSettings", "description": "Collection to store computational settings for the phonon computation.", "type": "object", "properties": {"npoints_band": {"title": "Npoints Band", "default": "number of points for band structure computation", "type": "integer"}, "kpath_scheme": {"title": "Kpath Scheme", "default": "indicates the kpath scheme", "type": "string"}, "kpoint_density_dos": {"title": "Kpoint Density Dos", "default": "number of points for computation of free energies and densities of states", "type": "integer"}}}'
    )
    assert np.round(output.phonon_bandstructure.bands[-1, 0], 2) == 14.41


def test_phonon_socket_flow(Si, tmp_path, mock_aims, species_dir):
    import numpy as np

    from jobflow import run_locally

    from atomate2_temp.aims.jobs.core import StaticMaker, RelaxMaker
    from atomate2_temp.aims.jobs.phonons import PhononDisplacementMakerSocket
    from atomate2_temp.aims.sets.core import StaticSetGenerator

    from atomate2_temp.aims.flows.phonons import PhononMaker

    # mapping from job name to directory containing test files
    ref_paths = {
        "Relaxation calculation": "phonon-relax-si",
        "phonon static aims 1/1": "phonon-disp-si",
        "SCF Calculation": "phonon-energy-si",
    }

    # settings passed to fake_run_aims; adjust these to check for certain input settings
    fake_run_aims_kwargs = {}

    # automatically use fake FHI-aims
    mock_aims(ref_paths, fake_run_aims_kwargs)

    parameters = {"k_grid": [2, 2, 2], "species_dir": species_dir.as_posix()}
    parameters_phonon_disp = dict(
        compute_forces=True, use_pimd_wrapper=("localhost", 12345), **parameters
    )

    # generate job

    maker = PhononMaker(
        bulk_relax_maker=RelaxMaker.full_relaxation(user_parameters=parameters),
        static_energy_maker=StaticMaker(
            input_set_generator=StaticSetGenerator(user_parameters=parameters)
        ),
        use_symmetrized_structure="primitive",
        socket=True,
        phonon_displacement_maker=PhononDisplacementMakerSocket(
            input_set_generator=StaticSetGenerator(
                user_parameters=parameters_phonon_disp,
                user_kpoints_settings={"density": 5.0, "even": True},
            )
        ),
    )
    maker.name = "phonons"
    flow = maker.make(
        MSONableAtoms(Si),
        supercell_matrix=np.array([-1, 1, 1, 1, -1, 1, 1, 1, -1]).reshape((3, 3)),
    )

    # run the flow or job and ensure that it finished running successfully
    os.chdir(tmp_path)
    responses = run_locally(flow, create_folders=True, ensure_success=True)
    os.chdir(cwd)

    # validation the outputs of the job
    output = responses[flow.job_uuids[-1]][1].output
    assert output.code == "aims"
    assert output.born is None
    assert not output.has_imaginary_modes

    assert output.temperatures == list(range(0, 500, 10))
    assert output.heat_capacities[0] == 0.0
    assert np.round(output.heat_capacities[-1], 2) == 23.06
    assert (
        output.phonopy_settings.schema_json()
        == '{"title": "PhononComputationalSettings", "description": "Collection to store computational settings for the phonon computation.", "type": "object", "properties": {"npoints_band": {"title": "Npoints Band", "default": "number of points for band structure computation", "type": "integer"}, "kpath_scheme": {"title": "Kpath Scheme", "default": "indicates the kpath scheme", "type": "string"}, "kpoint_density_dos": {"title": "Kpoint Density Dos", "default": "number of points for computation of free energies and densities of states", "type": "integer"}}}'
    )
    assert np.round(output.phonon_bandstructure.bands[-1, 0], 2) == 14.41


def test_phonon_default_flow(Si, tmp_path, mock_aims, species_dir):
    import numpy as np

    from jobflow import run_locally

    from atomate2_temp.aims.jobs.core import StaticMaker, RelaxMaker
    from atomate2_temp.aims.jobs.phonons import PhononDisplacementMaker

    from atomate2_temp.aims.sets.core import StaticSetGenerator

    from atomate2_temp.aims.flows.phonons import PhononMaker

    # mapping from job name to directory containing test files
    ref_paths = {
        "Relaxation calculation": "phonon-relax-default-si",
        "phonon static aims 1/1": "phonon-disp-default-si",
        "SCF Calculation": "phonon-energy-default-si",
    }

    # settings passed to fake_run_aims; adjust these to check for certain input settings
    fake_run_aims_kwargs = {}

    # automatically use fake FHI-aims
    mock_aims(ref_paths, fake_run_aims_kwargs)

    aims_sd = os.environ.get("AIMS_SPECIES_DIR", None)
    os.environ["AIMS_SPECIES_DIR"] = str(species_dir)

    maker = PhononMaker()
    maker.name = "phonons"
    flow = maker.make(
        MSONableAtoms(Si),
        supercell_matrix=np.array([-1, 1, 1, 1, -1, 1, 1, 1, -1]).reshape((3, 3)),
    )

    # run the flow or job and ensure that it finished running successfully
    os.chdir(tmp_path)
    responses = run_locally(flow, create_folders=True, ensure_success=True)
    os.chdir(cwd)

    # validation the outputs of the job
    output = responses[flow.job_uuids[-1]][1].output
    assert output.code == "aims"
    assert output.born is None
    assert not output.has_imaginary_modes

    assert output.temperatures == list(range(0, 500, 10))
    assert output.heat_capacities[0] == 0.0
    assert np.round(output.heat_capacities[-1], 2) == 22.85
    assert (
        output.phonopy_settings.schema_json()
        == '{"title": "PhononComputationalSettings", "description": "Collection to store computational settings for the phonon computation.", "type": "object", "properties": {"npoints_band": {"title": "Npoints Band", "default": "number of points for band structure computation", "type": "integer"}, "kpath_scheme": {"title": "Kpath Scheme", "default": "indicates the kpath scheme", "type": "string"}, "kpoint_density_dos": {"title": "Kpoint Density Dos", "default": "number of points for computation of free energies and densities of states", "type": "integer"}}}'
    )
    assert np.round(output.phonon_bandstructure.bands[-1, 0], 2) == 15.02

    if aims_sd is not None:
        os.environ["AIMS_SPECIES_DIR"] = aims_sd


def test_phonon_default_socket_flow(Si, tmp_path, mock_aims, species_dir):
    import numpy as np

    from jobflow import run_locally

    from atomate2_temp.aims.jobs.core import StaticMaker, RelaxMaker
    from atomate2_temp.aims.jobs.phonons import PhononDisplacementMakerSocket
    from atomate2_temp.aims.sets.core import StaticSetGenerator

    from atomate2_temp.aims.flows.phonons import PhononMaker

    aims_sd = os.environ.get("AIMS_SPECIES_DIR", None)
    os.environ["AIMS_SPECIES_DIR"] = str(species_dir)

    # mapping from job name to directory containing test files
    ref_paths = {
        "Relaxation calculation": "phonon-relax-default-si",
        "phonon static aims 1/1": "phonon-disp-default-si",
        "SCF Calculation": "phonon-energy-default-si",
    }

    # settings passed to fake_run_aims; adjust these to check for certain input settings
    fake_run_aims_kwargs = {}

    # automatically use fake FHI-aims
    mock_aims(ref_paths, fake_run_aims_kwargs)

    # generate job

    maker = PhononMaker(socket=True)
    maker.name = "phonons"
    flow = maker.make(
        MSONableAtoms(Si),
        supercell_matrix=np.array([-1, 1, 1, 1, -1, 1, 1, 1, -1]).reshape((3, 3)),
    )

    # run the flow or job and ensure that it finished running successfully
    os.chdir(tmp_path)
    responses = run_locally(flow, create_folders=True, ensure_success=True)
    os.chdir(cwd)

    # validation the outputs of the job
    output = responses[flow.job_uuids[-1]][1].output
    assert output.code == "aims"
    assert output.born is None
    assert not output.has_imaginary_modes

    assert output.temperatures == list(range(0, 500, 10))
    assert output.heat_capacities[0] == 0.0
    assert np.round(output.heat_capacities[-1], 2) == 22.85
    assert (
        output.phonopy_settings.schema_json()
        == '{"title": "PhononComputationalSettings", "description": "Collection to store computational settings for the phonon computation.", "type": "object", "properties": {"npoints_band": {"title": "Npoints Band", "default": "number of points for band structure computation", "type": "integer"}, "kpath_scheme": {"title": "Kpath Scheme", "default": "indicates the kpath scheme", "type": "string"}, "kpoint_density_dos": {"title": "Kpoint Density Dos", "default": "number of points for computation of free energies and densities of states", "type": "integer"}}}'
    )
    assert np.round(output.phonon_bandstructure.bands[-1, 0], 2) == 15.02

    if aims_sd is not None:
        os.environ["AIMS_SPECIES_DIR"] = aims_sd
