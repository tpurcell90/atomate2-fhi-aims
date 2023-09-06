"""Module defining base FHI-aims input set and generator."""
from __future__ import annotations

import copy
import json
import logging
from dataclasses import dataclass, field
from typing import Any, Iterable, Dict, List, Tuple, Sequence

import numpy as np

from monty.json import MontyEncoder, MontyDecoder
from fhi_aims_workflows.io.parsers import read_aims_output, AimsParseError
from fhi_aims_workflows.utils.pymatgen_core_io import (
    InputGenerator,
    InputSet,
    InputFile,
)
from fhi_aims_workflows.utils.MSONableAtoms import MSONableAtoms
from ase.calculators.aims import AimsTemplate
from ase.atoms import Atoms

from pathlib import Path

from fhi_aims_workflows.utils.common import (
    TMPDIR_NAME,
    CONTROL_FILE_NAME,
    GEOMETRY_FILE_NAME,
    PARAMS_JSON_FILE_NAME,
    cwd,
)

from warnings import warn

DEFAULT_AIMS_PROPERTIES = [
    "energy",
    "free_energy",
    "forces",
    "stress",
    "stresses",
    "dipole",
    "magmom",
]

__all__ = ["AimsInputSet", "AimsInputGenerator"]

logger = logging.getLogger(__name__)


class AimsInputFile(InputFile):
    def __init__(self, content_str):
        self._content_str = content_str

    def get_string(self) -> str:
        return self._content_str

    @classmethod
    def from_string(cls, contents: str):
        return cls(contents)


class AimsInputSet(InputSet):
    """
    A class to represent a set of Aims inputs.
    """

    def __init__(
        self,
        parameters: Dict[str, Any],
        atoms: Atoms,
        properties: Sequence[str] = ("energy", "free_energy"),
    ):
        self._parameters = parameters
        self._atoms = MSONableAtoms(atoms)
        self._properties = properties

        aims_control_in, aims_geometry_in = self.get_input_files()

        super().__init__(
            inputs={
                CONTROL_FILE_NAME: aims_control_in,
                GEOMETRY_FILE_NAME: aims_geometry_in,
                PARAMS_JSON_FILE_NAME: json.dumps(
                    self._parameters, indent=2, cls=MontyEncoder
                ),
            }
        )

    def get_input_files(self):
        with cwd(TMPDIR_NAME, mkdir=True, rmdir=True):
            aims_template = AimsTemplate()
            aims_template.write_input(
                Path("./"), self._atoms, self._parameters, self._properties
            )

            aims_control_in = AimsInputFile.from_file("control.in")
            aims_geometry_in = AimsInputFile.from_file("geometry.in")

        return aims_control_in, aims_geometry_in

    @property
    def control_in(self):
        """Get the AimsInput object."""
        return self[CONTROL_FILE_NAME]

    @property
    def geometry_in(self):
        """Get the AimsInput object."""
        return self[GEOMETRY_FILE_NAME]

    @property
    def parameters_json(self):
        """Get the AimsInput object."""
        return self[PARAMS_JSON_FILE_NAME]

    def set_parameters(self, *args, **kwargs) -> dict:
        """Set the parameters object for the AimsTemplate

        This sets the parameters object that is passed to an AimsTempalte and resets the control.in file

        One can pass a dictionary mapping the aims variables to their values or
        the aims variables as keyword arguments. A combination of the two
        options is also allowed.

        Returns
        -------
        dict
            dictionary with the variables that have been added.
        """
        self._parameters.clear()
        for arg in args:
            self._parameters.update(arg)

        self._parameters.update(kwargs)

        aims_control_in, _ = self.get_input_files()
        self.inputs[CONTROL_FILE_NAME] = aims_control_in
        self.inputs[PARAMS_JSON_FILE_NAME] = json.dumps(
            self._parameters, indent=2, cls=MontyEncoder
        )
        self.__dict__.update(self.inputs)

        return self._parameters

    def remove_parameters(self, keys: Iterable[str] | str, strict: bool = True) -> dict:
        """Remove the aims parameters listed in keys.

        This removes the aims variables from the parameters object.

        Parameters
        ----------
        keys
            string or list of strings with the names of the aims parameters
            to be removed.
        strict
            whether to raise a KeyError if one of the aims parameters to be
            removed is not present.

        Returns
        -------
        dict
            dictionary with the variables that have been removed.
        """
        if isinstance(keys, str):
            keys = [keys]
        for key in keys:
            if strict and key not in self._parameters:
                raise ValueError(f"The key ({key}) is not in self._parameters")
            del self._parameters[key]

        return self.set_parameters(self._parameters)

    def set_atoms(self, atoms: Atoms) -> Atoms:
        """Set the atoms object for this input set."""
        self._atoms = MSONableAtoms(atoms)

        _, aims_geometry_in = self.get_input_files()
        self.inputs[GEOMETRY_FILE_NAME] = aims_geometry_in
        self.__dict__.update(self.inputs)

        return self.aims_input.set_structure(atoms)

    def deepcopy(self):
        """Deep copy of the input set."""
        return copy.deepcopy(self)


@dataclass
class AimsInputGenerator(InputGenerator):
    """
    A class to generate Aims input sets.

    Parameters
    ----------
    user_parameters:
        Updates the default parameters for the FHI-aims calculator
    """

    user_parameters: dict = field(default_factory=dict)

    def get_input_set(  # type: ignore
        self,
        atoms: Atoms = None,
        prev_dir: str | Path = None,
        properties: List[str] | Tuple[str] = None,
    ) -> AimsInputSet:
        """Generate an AimsInputSet object.

        Parameters
        ----------
        atoms : Atoms
            ASE Atoms object.
        prev_dir: str or Path
            Path to the previous working directory
        properties: list or tuple of str
            System properties that are being calculated
        """
        prev_atoms, prev_parameters, prev_results = self._read_previous(prev_dir)
        atoms = atoms if atoms is not None else prev_atoms
        parameters = self._get_input_parameters(atoms, prev_parameters)
        properties = self._get_properties(properties, parameters, prev_results)

        return AimsInputSet(parameters=parameters, atoms=atoms, properties=properties)

    def _read_previous(
        self, prev_dir: str | Path = None
    ) -> tuple[Atoms, Dict[str, Any], Dict[str, Iterable[float]]]:
        """Read in previous results

        Parameters
        ----------
        prev_dir: str or Path
            The previous directory for the calculation
        """
        prev_atoms = None
        prev_parameters = {}
        prev_results = {}

        if prev_dir:
            print(f"Previous dir: {prev_dir}")
            prev_parameters = json.load(
                open(f"{prev_dir}/parameters.json", "rt"), cls=MontyDecoder
            )
            try:
                prev_atoms = read_aims_output(f"{prev_dir}/aims.out")
                prev_results = prev_atoms.calc.results
            except (IndexError, AimsParseError):
                pass

        return prev_atoms, prev_parameters, prev_results

    def _get_properties(
        self,
        properties: Iterable[str] = None,
        parameters: Dict[str, Any] = None,
        prev_results: Dict[str, Iterable[float]] = None,
    ) -> Iterable[str]:
        """Get the properties to calculate

        Parameters
        ----------
        properties
            The currently requested properties
        parameters
            The parameters for this calculation
        prev_results
            The previous calculation results

        Returns
        -------
        The list of properties to calculate
        """
        if properties is None:
            properties = ["energy", "free_energy"]

        for key in prev_results.keys():
            if key not in properties and key in DEFAULT_AIMS_PROPERTIES:
                properties.append(key)

        if "compute_forces" in parameters and "forces" not in properties:
            properties.append("forces")
        if "compute_heat_flux" in parameters and "stresses" not in properties:
            properties.append("stress")
            properties.append("stresses")
        if "stress" not in properties and (
            ("compute_analytical_stress" in parameters)
            or ("compute_numerical_stress" in parameters)
            or ("compute_heat_flux" in parameters)
        ):
            properties.append("stress")

        return properties

    def _get_input_parameters(
        self, atoms: Atoms, prev_parameters: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Create the input parameters

        Parameters
        ----------
        atoms: ase.atoms.Atoms
            The atoms object for the structures
        prev_parameters
            The previous calculation's calculation parameters

        Returns
        -------
        The input object
        """

        # Get the default configuration
        # FHI-aims recommends using their defaults so bare-bones default parameters
        parameters = {
            "xc": "pbe",
            "relativistic": "atomic_zora scalar",
        }

        # Override default parameters with previous parameters
        prev_parameters = {} if prev_parameters is None else prev_parameters
        prev_parameters.pop("relax_geometry", None)
        prev_parameters.pop("relax_unit_cell", None)

        parameters = recursive_update(parameters, prev_parameters)

        # Override default parameters with job-specific updates
        parameter_updates = self.get_parameter_updates(atoms, prev_parameters)
        parameters = recursive_update(parameters, parameter_updates)

        # Override default parameters with user_parameters
        parameters = recursive_update(parameters, self.user_parameters)

        if np.any(atoms.pbc) and ("k_grid" not in parameters):
            warn(
                "WARNING: the k_grid was not set, setting to a grid with a k-point density of 5.0"
            )
            parameters["k_grid"] = self.d2k(atoms)
        elif not np.any(atoms.pbc) and "k_grid" in parameters:
            warn("WARNING: removing unnecessary k_grid information")
            del parameters["k_grid"]

        return parameters

    def get_parameter_updates(
        self, atoms: Atoms, prev_parameters: Dict[str, Any]
    ) -> dict:
        """
        Updates the parameters for a given calculation type

        Parameters
        ----------
        atoms : Atoms
            ASE Atoms object.
        prev_parameters
            Previous calculation parameters.

        Returns
        -------
        dict
            A dictionary of updates to apply.
        """
        raise NotImplementedError

    def d2k(
        self, atoms: Atoms, kptdensity: float | Iterable[float] = 5.0, even: bool = True
    ) -> Iterable[float]:
        """Convert k-point density to Monkhorst-Pack grid size.

        inspired by [ase.calculators.calculator.kptdensity2monkhorstpack]

        Parameters
        ----------
        atoms: Atoms object
            Contains unit cell and information about boundary conditions.
        kptdensity: float or list of floats
            Required k-point density.  Default value is 5.0 point per Ang^-1.
        even: bool
            Round up to even numbers.

        Returns
        -------
        list
            Monkhorst-Pack grid size in all directions
        """
        recipcell = atoms.cell.reciprocal()
        return self.d2k_recipcell(recipcell, atoms.pbc, kptdensity, even)

    @staticmethod
    def d2k_recipcell(
        recipcell,
        pbc: List[bool],
        kptdensity: float | Iterable[float] = 5.0,
        even: bool = True,
    ) -> Iterable[float]:
        """Convert k-point density to Monkhorst-Pack grid size.

        Parameters
        ----------
        recipcell: ASE Cell object
            The reciprocal cell
        pbc: list of Bools
            If element of pbc is True then system is periodic in that direction
        kptdensity: float or list of floats
            Required k-point density.  Default value is 3.5 point per Ang^-1.
        even: bool
            Round up to even numbers.

        Returns
        -------
        list
            Monkhorst-Pack grid size in all directions
        """
        if not isinstance(kptdensity, list) and not isinstance(kptdensity, np.ndarray):
            kptdensity = 3 * [float(kptdensity)]
        kpts = []
        for i in range(3):
            if pbc[i]:
                k = (
                    2
                    * np.pi
                    * np.sqrt((recipcell[i] ** 2).sum())
                    * float(kptdensity[i])
                )
                if even:
                    kpts.append(2 * int(np.ceil(k / 2)))
                else:
                    kpts.append(int(np.ceil(k)))
            else:
                kpts.append(1)
        return kpts


def recursive_update(d: dict, u: dict):
    """
    Update a dictionary recursively and return it.

    Parameters
    ----------
        d: Dict
            Input dictionary to modify
        u: Dict
            Dictionary of updates to apply

    Returns
    -------
    Dict
        The updated dictionary.

    Example
    ----------
        d = {'activate_hybrid': {"hybrid_functional": "HSE06"}}
        u = {'activate_hybrid': {"cutoff_radius": 8}}

        yields {'activate_hybrid': {"hybrid_functional": "HSE06", "cutoff_radius": 8}}}
    """
    for k, v in u.items():
        if isinstance(v, dict):
            d[k] = recursive_update(d.get(k, {}), v)
        elif isinstance(v, list):
            old_v = d.get(k, [])
            d[k] = old_v + v
        else:
            d[k] = v
    return d
