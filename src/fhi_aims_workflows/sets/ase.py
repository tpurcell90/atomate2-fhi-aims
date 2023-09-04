"""Module defining base ASE input set and generator."""
from __future__ import annotations

import copy
import json
import logging
from dataclasses import dataclass, field
from typing import Any, Iterable, Dict, List

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
    ASE_JSON,
    cwd,
)

from warnings import warn


__all__ = ["ASEInputSet", "ASEInputGenerator"]

logger = logging.getLogger(__name__)


class ASEInputFile(InputFile):
    def __init__(self, content_str):
        self._content_str = content_str

    def get_string(self) -> str:
        return self._content_str

    @classmethod
    def from_string(cls, contents: str):
        return cls(contents)


class ASEInputSet(InputSet):
    """
    A class to represent a set of Aims inputs.
    """

    def __init__(
        self,
        parameters: Dict[str, Any],
        atoms: Atoms,
        properties: Iterable[str] = ("energy", "free_energy"),
        calc_name: str = "aims",
    ):
        self._parameters = parameters
        self._atoms = MSONableAtoms(atoms)
        self._properties = properties
        self._calc_name = calc_name

        ase_json = dict(
            parameters=self._parameters.copy(),
            calc_name=self._calc_name,
            atoms=self._atoms,
            properties=self._properties,
        )

        super().__init__(
            inputs={
                ASE_JSON: json.dumps(self.ase_json, indent=2, cls=MontyEncoder),
            }
        )

    @property
    def ase_json_file(self):
        """Get the AimsInput object."""
        return self[ASE_JSON]

    @property
    def ase_json(self):
        """Create an ASE_json file"""
        return dict(
            parameters=self._parameters.copy(),
            calc_name=self._calc_name,
            atoms=self._atoms,
            properties=self._properties,
        )

    def set_parameters(self, *args, **kwargs) -> dict:
        """Set the parameters object for the AimsTemplate

        This sets the parameters object that is passed to an AimsTempalte and resets the control.in file

        One can pass a dictionary mapping the abinit variables to their values or
        the abinit variables as keyword arguments. A combination of the two
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

        self.inputs[ASE_JSON] = json.dumps(self.ase_json, indent=2, cls=MontyEncoder)
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

        self.inputs[ASE_JSON] = json.dumps(self.ase_json, indent=2, cls=MontyEncoder)

        return self._atoms

    def deepcopy(self):
        """Deep copy of the input set."""
        return copy.deepcopy(self)


@dataclass
class ASEInputGenerator(InputGenerator):
    """
    A class to generate Aims input sets.

    Parameters
    ----------
    user_parameters:
        Updates the default parameters for the FHI-aims calculator
    config_dict
        The config dictionary to use containing the base input set settings.
    """

    user_parameters: dict = field(default_factory=dict)
    calc_name: str = field(default_factory=str)

    def get_input_set(  # type: ignore
        self,
        atoms: Atoms = None,
        prev_dir: str | Path = None,
        properties: Iterable[str] = None,
    ) -> ASEInputSet:
        """Generate an ASEInputSet object.

        Parameters
        ----------
        atoms : Atoms
            ASE Atoms object.
        prev_dir: str or Path
            Path to the previous working directory
        properties: iterable of str
            System properties that are being calculated
        """
        prev_atoms, prev_parameters, prev_results = self._read_previous(prev_dir)
        atoms = atoms if atoms is not None else prev_atoms
        parameters = self._get_input_paramesters(atoms, prev_parameters)
        properties = self._get_properties(properties, prev_results)

        return ASEInputSet(
            parameters=parameters,
            atoms=atoms,
            properties=properties,
        )

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
            prev_ase = json.load(
                open(f"{prev_dir}/ase_calc.json", "rt"), cls=MontyDecoder
            )
            prev_atoms = prev_ase["atoms"]
            prev_parameters = prev_ase["parameters"]
            if Path(f"{prev_dir}/results.json").exists():
                prev_results = json.load(
                    open(f"{prev_dir}/results.json", "rt"), cls=MontyDecoder
                )

        return prev_atoms, prev_parameters, prev_results

    def _get_properties(
        self,
        properties: Iterable[str] = None,
        prev_results: Dict[str, Iterable[float]] = None,
    ) -> Iterable[str]:
        """Get the properties to calculate

        Parameters
        ----------
        properties
            The currently requested properties
        prev_results
            The previous calculation results

        Returns
        -------
        The list of properties to calculate
        """
        if properties is None:
            properties = ["energy", "free_energy"]

        for key in prev_results.keys():
            if key not in properties:
                properties.append(key)

        return properties

    def _get_input_paramesters(
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
        parameters = {}

        # Override default parameters with previous parameters
        prev_parameters = {} if prev_parameters is None else prev_parameters
        parameters = recursive_update(parameters, prev_parameters)

        # Override default parameters with job-specific updates
        parameter_updates = self.get_parameter_updates(atoms, prev_parameters)
        parameters = recursive_update(parameters, parameter_updates)

        # Override default parameters with user_parameters
        parameters = recursive_update(parameters, self.user_parameters)

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
        return dict()


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
        else:
            d[k] = v
    return d
