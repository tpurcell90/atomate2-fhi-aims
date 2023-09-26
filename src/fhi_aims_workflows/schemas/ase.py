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
from fhi_aims_workflows.utils import datetime_str
from fhi_aims_workflows.utils.MSONableAtoms import MSONableAtoms


class ASEInputsSummary(BaseModel):
    structure: Structure = Field(None, description="pymatgen Structure of the atoms")
    molecule: Molecule = Field(None, description="pymatgen Molecule of the atoms")
    calculator_name: str = Field(None, description="The name of the ASE calculator")
    calculator_parameters: Dict[str, Any] = Field(
        None, description="The the parameters for the ASE calculator"
    )

    @classmethod
    def from_input_set(cls, input_set):
        structure, molecule = input_set.atoms.pymatgen_pair
        return ASEInputsSummary(
            structure,
            molecule,
            input_set.calc_name,
            input_set.calc_parameters,
        )

    @classmethod
    def from_atoms(cls, atoms):
        structure, molecule = atoms.pymatgen_pair
        return ASEInputsSummary(
            structure,
            molecule,
            atoms.calc.name,
            atoms.calc.parameters,
        )


class ASEOutputSummary(BaseModel):
    """Document defining and ASE Caclculation output"""

    energy: float = Field(
        None, description="The final total DFT energy for the calculation."
    )

    free_energy: float = Field(
        None, description="The final total DFT free energy for the calculation."
    )

    forces: List[Vector3D] = Field(
        None, description="The final DFT forces for the calculation."
    )

    stress: Matrix3D = Field(
        None, description="The final DFT stress for the calculation."
    )

    stresses: List[Matrix3D] = Field(
        None, description="The final DFT per atom stresses for the calculation."
    )

    dipole: Vector3D = Field(
        None, description="The final DFT dipole moment for the calculation."
    )

    charges: List[float] = Field(
        None, description="The final DFT charges for the calculation."
    )

    magmom: float = Field(
        None, description="The final DFT magnetic moment for the calculation."
    )

    magmoms: List[float] = Field(
        None, description="The final DFT local magnetic moments for the calculation."
    )

    energies: List[float] = Field(
        None, description="The final DFT per atom energies for the calculation."
    )

    dielectric_tensor: Matrix3D = Field(
        None, description="The final DFT dielectric tensors for the calculation."
    )

    born_effective_charges: List[Matrix3D] = Field(
        None, description="The final DFT Born effective charges for the calculation."
    )

    polarization: Vector3D = Field(
        None, description="The final DFT polarization for the calculation."
    )

    atoms: MSONableAtoms = Field(
        None, description="The atoms object used for the calculation"
    )
    structure: Structure = Field(None, description="pymatgen Structure of the atoms")
    molecule: Molecule = Field(None, description="pymatgen Molecule of the atoms")

    @classmethod
    def from_atoms(cls, atoms: MSONableAtoms):
        """Create and ASEOutput from the atoms object

        Properties
        ----------
        atoms: MSONableAtoms
            The atoms object used for the ASE calculation
        calc_name: str
            The name of the calculator used for the ASE calculation
        calc_parameters: dict
            The calculator parameters for the ASE calculation
        """
        if atoms.calc:
            results = atoms.calc.results
        else:
            results = {}

        structure, molecule = atoms.pymatgen_pair

        if results.get("stress", None):
            stress = voigt_6_to_full_3x3_stress(results.get("stress"))
        else:
            stress = None

        if results.get("stresses", None):
            stresses = [
                voigt_6_to_full_3x3_stress(st) for st in results.get("stresses", None)
            ]
        else:
            stresses = None

        return cls(
            energy=results.get("energy", None),
            free_energy=results.get("free_energy", None),
            forces=results.get("forces", None),
            stress=stress,
            stresses=stresses,
            dipole=results.get("dipole", None),
            charges=results.get("charges", None),
            magmom=results.get("magmom", None),
            magmoms=results.get("magmoms", None),
            energies=results.get("energies", None),
            dielectric_tensor=results.get("dielectric_tensor", None),
            born_effective_charges=results.get("born_effective_charges", None),
            polarization=results.get("polarization", None),
            atoms=atoms,
            structure=structure,
            molecule=molecule,
        )


class TaskDocument(StructureMetadata, MoleculeMetadata):
    dir_name: str = Field(None, description="The directory for this ASE task")

    last_updated: str = Field(
        default_factory=datetime_str,
        description="Timestamp for this task document was last updated",
    )

    completed_at: str = Field(
        default_factory=datetime_str,
        description="Timestamp for when this task was completed",
    )

    input: ASEInputsSummary = Field(
        None, description="The input to the first calculation"
    )

    output: ASEOutputSummary = Field(
        None, description="The output of the final calculation"
    )

    structure: Structure = Field(
        None, description="Final output structure from the task"
    )

    atoms: MSONableAtoms = Field(None, description="Final output atoms from the task")

    state: Status = Field(None, description="State of this task")

    included_atoms: List[MSONableAtoms] = Field(
        None, description="List of FHI-aims objects included with this task document"
    )

    entry: ComputedEntry = Field(
        None, description="The ComputedEntry from the task doc"
    )

    task_label: str = Field(None, description="A description of the task")

    tags: List[str] = Field(None, description="Metadata tags for this task document")

    author: str = Field(None, description="Author extracted from transformations")

    icsd_id: str = Field(
        None, description="International crystal structure database id of the structure"
    )

    atoms_list: List[MSONableAtoms] = Field(
        None, description="The inputs and outputs for all FHI-aims runs in this task."
    )

    transformations: Dict[str, Any] = Field(
        None,
        description="Information on the structural transformations, parsed from a "
        "transformations.json file",
    )

    additional_json: Dict[str, Any] = Field(
        None, description="Additional json loaded from the calculation directory"
    )

    @classmethod
    def from_atoms(
        cls: Type[_T], atoms: MSONableAtoms, additional_fields: Dict[str, Any] = None
    ):
        if not additional_fields:
            additional_fields = {}

        input_summary = ASEInputsSummary.from_atoms(atoms)
        output_summary = ASEOutputSummary.from_atoms(atoms)
        structure = input_summary.structure
        if not structure:
            structure = input_summary.molecule
        return cls(
            dir_name=None,
            input=input_summary,
            output=output_summary,
            structure=structure,
            atoms=input_summary.atoms,
            state=None,
            included_atoms=[input_summary.atoms],
            entry=cls.get_entry([atoms]),
            tags=additional_fields.get("tags", [""]),
            atoms_list=[atoms],
        )

    @staticmethod
    def get_entry(
        atoms_list: List[MSONableAtoms], job_id: Optional[str] = None
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
            "composition": atoms_list[-1].get_chemical_formula(),
            "energy": atoms_list[-1].get_potential_energy(),
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
