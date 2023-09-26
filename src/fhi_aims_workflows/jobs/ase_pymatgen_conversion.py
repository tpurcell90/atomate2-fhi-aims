from pymatgen.core.structure import Structure, Molecule
from pymatgen.io.ase import AseAtomsAdaptor

from dataclasses import dataclass, field

from jobflow import job, Response

from fhi_aims_workflows.utils.MSONableAtoms import MSONableAtoms
from fhi_aims_workflows.schemas.ase import ASEOutput

from typing import List, Dict


@job
def convert_mult_to_structure(atoms_list: List[MSONableAtoms]) -> Response:
    """Convert from an ASE Atoms Object to a pymatgen structure

    Parameters
    ----------
    atoms_list: List of atoms to convert
        The list of Atoms objects to convert

    Returns
    -------
    Response the converts all structures in atoms_list to structures
    """
    return Response(detour=[convert_to_structure(at) for at in atoms_list])


@job
def convert_to_structure(atoms: MSONableAtoms) -> Response:
    """Convert from an ASE Atoms Object to a pymatgen structure

    Parameters
    ----------
    atoms
        The Atoms object to convert

    Returns
    -------
    The the ASEOutput objects Response
    """
    return Response(output=ASEOutput.from_atoms(atoms))


@job
def convert_to_atoms(structure: Structure | Molecule) -> MSONableAtoms:
    """Convert from a pymatgen structure to an ASE Atoms object

    Parameters
    ----------
    structure
        The pymatgen Structure to convert

    Returns
    -------
    The ASE Atoms object
    """
    return MSONableAtoms(ASE_ADAPTOR.get_atoms(structure))
