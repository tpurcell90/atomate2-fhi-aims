"""A definition of a MSON document representing an FHI-aims task"""

import logging
from pathlib import Path
from typing import Union, List, Dict, Any, Type, TypeVar, Tuple, Optional

import numpy as np
from emmet.core.math import Vector3D, Matrix3D
from emmet.core.structure import StructureMetadata, MoleculeMetadata
from emmet.core.tasks import get_uri
from pydantic import Field, BaseModel
from pymatgen.entries.computed_entries import ComputedEntry

from fhi_aims_workflows.schemas.calculation import Status, AimsObject, Calculation
from fhi_aims_workflows.utils import datetime_str, MSONableAtoms

_T = TypeVar("_T", bound="TaskDocument")
_VOLUMETRIC_FILES = ("total_density", "spin_density", "eigenstate_density")
logger = logging.getLogger(__name__)


class AnalysisSummary(BaseModel):
    """Calculation relaxation summary."""

    delta_volume: float = Field(None, description="Absolute change in volume")
    delta_volume_as_percent: float = Field(
        None, description="Percentage change in volume"
    )
    max_force: float = Field(None, description="Maximum force on the atoms")
    errors: List[str] = Field(None, description="Errors from the FHI-aims output")

    @classmethod
    def from_aims_calc_docs(cls, calc_docs: List[Calculation]) -> "AnalysisSummary":
        """
        Create analysis summary from FHI-aims calculation documents.

        Parameters
        ----------
        calc_docs
            FHI-aims calculation documents.

        Returns
        -------
        AnalysisSummary
            Summary object
        """

        errors = []

        delta_vol = None
        percent_delta_vol = None

        final_calc = calc_docs[-1]
        max_force = None
        if final_calc.has_aims_completed == Status.SUCCESS:
            # max force and valid structure checks
            # structure = final_calc.output.structure
            max_force = _get_max_force(final_calc)
            # if not structure.is_valid():
            #     errors.append("Bad structure (atoms are too close!)")

        return cls(
            delta_volume=delta_vol,
            delta_volume_as_percent=percent_delta_vol,
            max_force=max_force,
            errors=errors,
        )


class Species(BaseModel):
    """A representation of the most important information about each type of species."""

    element: str = Field(None, description="Element assigned to this atom kind")
    species_defaults: str = Field(None, description="Basis set for this atom kind")


class SpeciesSummary(BaseModel):
    """A summary of species defaults."""

    species_defaults: Dict[str, Species] = Field(
        None, description="Dictionary mapping atomic kind labels to their info"
    )

    @classmethod
    def from_species_info(cls, species_info: dict):
        """Initialize from the atomic_kind_info dictionary."""
        d: Dict[str, Dict[str, Any]] = {"species_defaults": {}}
        for kind, info in species_info.items():
            d["species_defaults"][kind] = {
                "element": info["element"],
                "species_defaults": info["species_defaults"],
            }
        return cls(**d)


class InputSummary(BaseModel):
    """Summary of inputs for an FHI-aims calculation."""

    structure: MSONableAtoms = Field(
        None, description="The input structure object"
    )

    species_info: SpeciesSummary = Field(
        None, description="Summary of the species defaults used for each atom kind"
    )
    xc: str = Field(
        None, description="Exchange-correlation functional used if not the default"
    )

    @classmethod
    def from_aims_calc_doc(cls, calc_doc: Calculation) -> "InputSummary":
        """
        Create calculation input summary from a calculation document.

        Parameters
        ----------
        calc_doc
            An FHI-aims calculation document.

        Returns
        -------
        InputSummary
            A summary of the input structure and parameters.
        """
        summary = SpeciesSummary.from_species_info(
            calc_doc.input.species_info
        )

        return cls(
            structure=calc_doc.input.structure,
            atomic_kind_info=summary,
            xc=str(calc_doc.run_type),
        )


class OutputSummary(BaseModel):
    """Summary of the outputs for an FHI-aims calculation."""

    structure: MSONableAtoms = Field(
        None, description="The output structure object"
    )
    energy: float = Field(
        None, description="The final total DFT energy for the last calculation"
    )
    energy_per_atom: float = Field(
        None, description="The final DFT energy per atom for the last calculation"
    )
    bandgap: float = Field(None, description="The DFT bandgap for the last calculation")
    cbm: float = Field(None, description="CBM for this calculation")
    vbm: float = Field(None, description="VBM for this calculation")
    forces: List[Vector3D] = Field(
        None, description="Forces on atoms from the last calculation"
    )
    stress: Matrix3D = Field(
        None, description="Stress on the unit cell from the last calculation"
    )

    @classmethod
    def from_aims_calc_doc(cls, calc_doc: Calculation) -> "OutputSummary":
        """
        Create a summary of FHI-aims calculation outputs from an FHI-aims calculation document.

        Parameters
        ----------
        calc_doc
            An FHI-aims calculation document.

        Returns
        -------
        OutputSummary
            The calculation output summary.
        """
        # if calc_doc.output.ionic_steps:
        #     forces = calc_doc.output.ionic_steps[-1].get("forces", None)
        #     stress = calc_doc.output.ionic_steps[-1].get("stress", None)
        # else:
        forces = None
        stress = None
        return cls(
            structure=calc_doc.output.structure,
            energy=calc_doc.output.energy,
            energy_per_atom=calc_doc.output.energy_per_atom,
            bandgap=calc_doc.output.bandgap,
            cbm=calc_doc.output.cbm,
            vbm=calc_doc.output.vbm,
            forces=forces,
            stress=stress,
        )


class TaskDocument(StructureMetadata, MoleculeMetadata):
    """Definition of FHI-aims task document."""

    dir_name: str = Field(None, description="The directory for this FHI-aims task")
    last_updated: str = Field(
        default_factory=datetime_str,
        description="Timestamp for this task document was last updated",
    )
    completed_at: str = Field(
        None, description="Timestamp for when this task was completed"
    )
    input: InputSummary = Field(None, description="The input to the first calculation")
    output: OutputSummary = Field(
        None, description="The output of the final calculation"
    )
    structure: MSONableAtoms = Field(
        None, description="Final output structure from the task"
    )
    state: Status = Field(None, description="State of this task")
    included_objects: List[AimsObject] = Field(
        None, description="List of FHI-aims objects included with this task document"
    )
    aims_objects: Dict[AimsObject, Any] = Field(
        None, description="FHI-aims objects associated with this task"
    )
    entry: ComputedEntry = Field(
        None, description="The ComputedEntry from the task doc"
    )
    analysis: AnalysisSummary = Field(
        None, description="Summary of structural relaxation and forces"
    )
    task_label: str = Field(None, description="A description of the task")
    tags: List[str] = Field(None, description="Metadata tags for this task document")
    author: str = Field(None, description="Author extracted from transformations")
    icsd_id: str = Field(
        None, description="International crystal structure database id of the structure"
    )
    calcs_reversed: List[Calculation] = Field(
        None, description="The inputs and outputs for all FHI-aims runs in this task."
    )
    transformations: Dict[str, Any] = Field(
        None,
        description="Information on the structural transformations, parsed from a "
        "transformations.json file",
    )
    custodian: Any = Field(
        None,
        description="Information on the custodian settings used to run this "
        "calculation, parsed from a custodian.json file",
    )
    additional_json: Dict[str, Any] = Field(
        None, description="Additional json loaded from the calculation directory"
    )

    @classmethod
    def from_directory(
        cls: Type[_T],
        dir_name: Union[Path, str],
        volumetric_files: Tuple[str, ...] = _VOLUMETRIC_FILES,
        # store_additional_json: bool = SETTINGS.AIMS_STORE_ADDITIONAL_JSON,
        additional_fields: Dict[str, Any] = None,
        **aims_calculation_kwargs,
    ) -> _T:
        """
        Create a task document from a directory containing FHi-aims files.

        Parameters
        ----------
        dir_name
            The path to the folder containing the calculation outputs.
        # store_additional_json
        #     Whether to store additional json files found in the calculation directory.
        volumetric_files
            A volumetric files to search for.
        additional_fields
            Dictionary of additional fields to add to output document.
        **aims_calculation_kwargs
            Additional parsing options that will be passed to the
            :obj:`.Calculation.from_aims_files` function.

        Returns
        -------
        AimsTaskDoc
            A task document for the calculation.
        """
        logger.info(f"Getting task doc in: {dir_name}")

        additional_fields = {} if additional_fields is None else additional_fields
        dir_name = Path(dir_name)
        task_files = _find_aims_files(dir_name, volumetric_files=volumetric_files)

        if len(task_files) == 0:
            raise FileNotFoundError("No FHI-aims files found!")

        calcs_reversed = []
        all_aims_objects = []
        for task_name, files in task_files.items():
            calc_doc, aims_objects = Calculation.from_aims_files(
                dir_name, task_name, **files, **aims_calculation_kwargs
            )
            calcs_reversed.append(calc_doc)
            all_aims_objects.append(aims_objects)

        analysis = AnalysisSummary.from_aims_calc_docs(calcs_reversed)
        # transformations, icsd_id, tags, author = parse_transformations(dir_name)
        # if tags:
        #     tags.extend(additional_fields.get("tags", []))
        # else:
        tags = additional_fields.get("tags")

        # custodian = parse_custodian(dir_name)
        # orig_inputs = _parse_orig_inputs(dir_name)

        # additional_json = None
        # if store_additional_json:
        #     additional_json = parse_additional_json(dir_name)

        dir_name = get_uri(dir_name)  # convert to full uri path

        # only store objects from last calculation
        # TODO: make this an option
        aims_objects = all_aims_objects[-1]
        included_objects = None
        if aims_objects:
            included_objects = list(aims_objects.keys())

        # rewrite the original structure save!

        data = {
            "structure": calcs_reversed[-1].output.structure,
            "meta_structure": calcs_reversed[-1].output.structure,
            "dir_name": dir_name,
            "calcs_reversed": calcs_reversed,
            "analysis": analysis,
            # "transformations": transformations,
            # "custodian": custodian,
            # "orig_inputs": orig_inputs,
            # "additional_json": additional_json,
            # "icsd_id": icsd_id,
            "tags": tags,
            # "author": author,
            "completed_at": calcs_reversed[-1].completed_at,
            # "input": InputSummary.from_aims_calc_doc(calcs_reversed[0]),
            "output": OutputSummary.from_aims_calc_doc(calcs_reversed[-1]),
            "state": _get_state(calcs_reversed, analysis),
            "entry": cls.get_entry(calcs_reversed),
            "aims_objects": aims_objects,
            "included_objects": included_objects,
        }
        # doc = cls(**ddict)
        # doc = doc.copy(update=data)
        doc = cls(**data)
        return doc.copy(update=additional_fields)

    @staticmethod
    def get_entry(
        calc_docs: List[Calculation], job_id: Optional[str] = None
    ) -> ComputedEntry:
        """
        Get a computed entry from a list of FHI-aims calculation documents.

        Parameters
        ----------
        calc_docs
            A list of FHI-aims calculation documents.
        job_id
            The job identifier.

        Returns
        -------
        ComputedEntry
            A computed entry.
        """
        entry_dict = {
            "correction": 0.0,
            "entry_id": job_id,
            "composition": calc_docs[-1].output.structure.get_chemical_formula(),
            "energy": calc_docs[-1].output.energy,
            "parameters": {
                # Required to be compatible with MontyEncoder for the ComputedEntry
                # "run_type": str(calc_docs[-1].run_type),
                "run_type": "AIMS run"
            },
            "data": {
                "last_updated": datetime_str(),
            },
        }
        return ComputedEntry.from_dict(entry_dict)


def _find_aims_files(
    path: Union[str, Path],
    volumetric_files: Tuple[str, ...] = _VOLUMETRIC_FILES,
) -> Dict[str, Any]:
    """
    Find FHI-aims files in a directory.

    Only files in folders with names matching a task name (or alternatively files
    with the task name as an extension, e.g., aims.out) will be returned.

    CP2K files in the current directory will be given the task name "standard".

    Parameters
    ----------
    path
        Path to a directory to search.
    volumetric_files
        Volumetric files to search for.

    Returns
    -------
    dict[str, Any]
        The filenames of the calculation outputs for each FHI-aims task, given as a ordered
        dictionary of::

            {
                task_name: {
                    "aims_output_file": aims_output_filename,
                    "volumetric_files": [v_hartree file, e_density file, etc],
    """
    task_names = ["precondition"] + [f"relax{i}" for i in range(9)]
    path = Path(path)
    task_files = {}

    def _get_task_files(files, suffix=""):
        aims_files = {}
        vol_files = []
        for file in files:
            # Here we make assumptions about the output file naming
            if file.match(f"*aims.out{suffix}*"):
                aims_files["aims_output_file"] = Path(file).name
        for vol in volumetric_files:
            _files = [f.name for f in files if f.match(f"*{vol}*cube{suffix}*")]
            # _files.sort(key=natural_keys, reverse=True)
            if _files:
                vol_files.append(_files[0])

        if len(vol_files) > 0:
            # add volumetric files if some were found or other cp2k files were found
            aims_files["volumetric_files"] = vol_files

        return aims_files

    for task_name in task_names:
        subfolder_match = list(path.glob(f"{task_name}/*"))
        suffix_match = list(path.glob(f"*.{task_name}*"))
        if len(subfolder_match) > 0:
            # subfolder match
            task_files[task_name] = _get_task_files(subfolder_match)
        elif len(suffix_match) > 0:
            # try extension schema
            task_files[task_name] = _get_task_files(
                suffix_match, suffix=f".{task_name}"
            )

    if len(task_files) == 0:
        # get any matching file from the root folder
        standard_files = _get_task_files(list(path.glob("*")))
        if len(standard_files) > 0:
            task_files["standard"] = standard_files

    return task_files


def _get_max_force(calc_doc: Calculation) -> Optional[float]:
    """Get max force acting on atoms from a calculation document."""
    forces = None
    # forces = (
    #     calc_doc.output.ionic_steps[-1].get("forces")
    #     if calc_doc.output.ionic_steps
    #     else None
    # )
    # structure = calc_doc.output.structure
    if forces:
        forces = np.array(forces)
        # sdyn = structure.site_properties.get("selective_dynamics")
        # if sdyn:
        #     forces[np.logical_not(sdyn)] = 0
        return max(np.linalg.norm(forces, axis=1))
    return None


def _get_state(calc_docs: List[Calculation], analysis: AnalysisSummary) -> Status:
    """Get state from calculation documents and relaxation analysis."""
    all_calcs_completed = all(c.has_aims_completed == Status.SUCCESS for c in calc_docs)
    if len(analysis.errors) == 0 and all_calcs_completed:
        return Status.SUCCESS  # type: ignore
    return Status.FAILED  # type: ignore
