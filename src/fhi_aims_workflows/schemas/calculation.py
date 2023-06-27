"""Schemas for FHI-aims calculation objects"""

import os
from datetime import datetime

from pydantic import BaseModel
from jobflow.utils import ValueEnum
from pymatgen.electronic_structure.dos import Dos


__all__ = [
    'Status',
    'AimsObject',
    'Calculation'
]


class Status(ValueEnum):
    """FHI-aims calculation state."""

    SUCCESS = "successful"
    FAILED = "failed"


class AimsObject(ValueEnum):
    """Types of FHI-aims data objects."""

    DOS = "dos"
    BAND_STRUCTURE = "band_structure"
    ELECTRON_DENSITY = "electron_density"  # e_density
    WFN = "wfn"  # Wavefunction file



class Calculation(BaseModel):
    """Full FHI-aims calculation inputs and outputs."""

    dir_name: str = Field(None, description="The directory for this FHI-aims calculation")
    aims_version: str = Field(
        None, description="FHI-aims version used to perform the calculation"
    )
    has_aims_completed: Status = Field(
        None, description="Whether FHI-aims completed the calculation successfully"
    )
    input: CalculationInput = Field(
        None, description="FHI-aims input settings for the calculation"
    )
    output: CalculationOutput = Field(None, description="The FHI-aims calculation output")
    completed_at: str = Field(
        None, description="Timestamp for when the calculation was completed"
    )
    # task_name: str = Field(
    #     None, description="Name of task given by custodian (e.g., relax1, relax2)"
    # )
    output_file_paths: Dict[str, str] = Field(
        None,
        description="Paths (relative to dir_name) of the FHI-aims output files "
        "associated with this calculation",
    )
    # run_type: RunType = Field(
    #     None, description="Calculation run type (e.g., HF, HSE06, PBE)"
    # )
    # task_type: TaskType = Field(
    #     None, description="Calculation task type (e.g., Structure Optimization)."
    # )
    # calc_type: CalcType = Field(
    #     None, description="Return calculation type (run type + task_type)."
    # )

    @classmethod
    def from_aims_files(
        cls,
        dir_name: Union[Path, str],
        task_name: str,
        aims_output_file: Union[Path, str] = "aims.out",
        volumetric_files: List[str] = None,
        parse_dos: Union[str, bool] = False,
        parse_bandstructure: Union[str, bool] = False,
        average_v_hartree: bool = True,
        # run_bader: bool = (SETTINGS.AIMS_RUN_BADER and _BADER_EXE_EXISTS),
        strip_bandstructure_projections: bool = False,
        strip_dos_projections: bool = False,
        store_trajectory: bool = False,
        store_scf: bool = False,
        store_volumetric_data: Optional[
            Tuple[str]
        ] = SETTINGS.AIMS_STORE_VOLUMETRIC_DATA,
    ) -> Tuple["Calculation", Dict[AimsObject, Dict]]:
        """
        Create an FHI-aims calculation document from a directory and file paths.

        Parameters
        ----------
        dir_name
            The directory containing the calculation outputs.
        task_name
            The task name.
        aims_output_file
            Path to the main output of aims job, relative to dir_name.
        volumetric_files
            Path to volumetric (Cube) files, relative to dir_name.
        parse_dos
            Whether to parse the DOS. Can be:

            - "auto": Only parse DOS if there are no ionic steps.
            - True: Always parse DOS.
            - False: Never parse DOS.

        parse_bandstructure
            How to parse the bandstructure. Can be:

            - "auto": Parse the bandstructure with projections for NSCF calculations
              and decide automatically if it's line or uniform mode.
            - "line": Parse the bandstructure as a line mode calculation with
              projections
            - True: Parse the bandstructure as a uniform calculation with
              projections .
            - False: Parse the band structure without projects and just store
              vbm, cbm, band_gap, is_metal and efermi rather than the full
              band structure object.

        strip_dos_projections : bool
            Whether to strip the element and site projections from the density of
            states. This can help reduce the size of DOS objects in systems with
            many atoms.
        strip_bandstructure_projections : bool
            Whether to strip the element and site projections from the band structure.
            This can help reduce the size of DOS objects in systems with many atoms.
        store_trajectory:
            Whether to store the ionic steps as a pmg trajectory object, which can be
            pushed, to a bson data store, instead of as a list od dicts. Useful for
            large trajectories.
        store_scf:
            Whether to store the SCF convergence data.
        store_volumetric_data
            Which volumetric files to store.

        Returns
        -------
        Calculation
            An FHI-aims calculation document.
        """
        dir_name = Path(dir_name)
        aims_output_file = dir_name / aims_output_file

        volumetric_files = [] if volumetric_files is None else volumetric_files
        aims_output = AimsOutput(aims_output_file, auto_load=True)
        completed_at = str(datetime.fromtimestamp(os.stat(aims_output_file).st_mtime))

        output_file_paths = _get_output_file_paths(volumetric_files)
        aims_objects: Dict[AimsObject, Any] = _get_volumetric_data(
            dir_name, output_file_paths, store_volumetric_data
        )

        dos = _parse_dos(parse_dos, aims_output)
        if dos is not None:
            if strip_dos_projections:
                dos = Dos(dos.efermi, dos.energies, dos.densities)
            aims_objects[AimsObject.DOS] = dos  # type: ignore

        bandstructure = _parse_bandstructure(parse_bandstructure, aims_output)
        if bandstructure is not None:
            if strip_bandstructure_projections:
                bandstructure.projections = {}
            aims_objects[AimsObject.BANDSTRUCTURE] = bandstructure  # type: ignore

        input_doc = CalculationInput.from_aims_output(aims_output)
        output_doc = CalculationOutput.from_aims_output(
            aims_output, store_scf=store_scf
        )

        has_aims_completed = Status.SUCCESS if aims_output.completed else Status.FAILED

        if store_trajectory:
            traj = _parse_trajectory(aims_output=aims_output)
            aims_objects[AimsObject.TRAJECTORY] = traj  # type: ignore

        return (
            cls(
                dir_name=str(dir_name),
                task_name=task_name,
                aims_version=aims_output.aims_version,
                has_aims_completed=has_aims_completed,
                completed_at=completed_at,
                input=input_doc,
                output=output_doc,
                output_file_paths={
                    k.name.lower(): v for k, v in output_file_paths.items()
                },
                # run_type=run_type(input_doc.dict()),
                # task_type=task_type(input_doc.dict()),
                # calc_type=calc_type(input_doc.dict()),
            ),
            aims_objects,
        )
