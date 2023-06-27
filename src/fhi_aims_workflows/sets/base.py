"""Module defining base abinit input set and generator."""
from __future__ import annotations

import copy
import json
import logging
import os
from collections import namedtuple
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Iterable, Dict

import numpy as np

from monty.json import MontyEncoder, jsanitize
from fhi_aims_workflows.utils.pymatgen_core_io import (
    InputGenerator,
    InputSet,
    InputFile,
)
from fhi_aims_workflows.utils.MSONableAtoms import MSONableAtoms

from pymatgen.symmetry.bandstructure import HighSymmKpath

from ase.calculators.aims import AimsTemplate
from ase.atoms import Atoms

from pathlib import Path

from atomate2 import SETTINGS
from atomate2.abinit.files import fname2ext, load_aims_input, out_to_in
from atomate2.abinit.utils.common import (
    TMPDIR_NAME,
    OUTPUT_FILE_NAME,
    CONTROL_FILE_NAME,
    GEOMETRY_FILE_NAME,
    PARAMS_JSON_FILE_NAME,
)

import json
DEFAULT_AIMS_PROPERTIES = [
    "energy",
    "free_energy",
    "forces",
    "stress",
    "stresses",
    "dipole",
    "magmom",
]
_BASE_AIMS_SET = loadfn(resource_filename("fhi_aims_workflows.sets", "BaseAimsSet.yaml"))

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
        properties: Iterable[str] = ["energy", "free_energy"],
    ):
        self._parameters = parameters
        self._atoms = MSONableAtoms(atoms)

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
        atoms = self._atoms.atoms
        with cwd(TMPDIR_NAME, mkdir=True):
            aims_template = AimsTemplate()
            aims_template.write_input(Path("./"), atoms, self._parameters, properties)

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

        aims_control_in, _ = self.get_input_files()
        self.inputs[CONTROL_FILE_NAME] = aims_control_in
        self[CONTROL_FILE_NAME] = aims_control_in

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
            keys = [key]
        for key in keys:
            if strict and key not in self._parameters:
                raise ValueError(f"The key ({key}) is not in self._parameters")
            del self._parameters[key]

        return self.set_parameters(self._parameters)

    def set_atoms(self, atoms: Atoms) -> Atoms:
        """Set the atoms object for this input set."""
        self._atoms = atoms.todict()
        _, aims_geometry_in = self.get_input_files()
        self.inputs[GEOMETRY_FILE_NAME] = aims_geometry_in
        self[GEOMETRY_FILE_NAME] = aims_geometry_in

        return self.aims_input.set_structure(structure)

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
    config_dict
        The config dictionary to use containing the base input set settings.


    """
    user_parameters: dict = field(default_factory=dict)
    config_dict: dict = field(default_factory=lambda: _BASE_AIMS_INPUT_SET)

    symprec: float = SETTINGS.SYMPREC

    def get_input_set(  # type: ignore
        self,
        atoms: Atoms = None,
        prev_dir: str | Path = None,
        properties: Iterable[str] = None,
    ) -> AimsInputSet:
        """Generate an AimsInputSet object.

        Parameters
        ----------
        atoms : Atoms
            ASE Atoms object.
        pref_dir: str or Path
            Path to the previous working directory
        """
        prev_atoms, prev_parameters, prev_results = self._read_previous(prev_dir)
        atoms = atoms if atoms is not None else prev_atoms
        parameters = self._get_input_paramesters(prev_parameters)
        properties = ["energy", "free_energy"]

        for key in prev_results.keys():
            if key not in properties and key in DEFAULT_AIMS_PROPERTIES:
                properties.append(key)

        return AimsInputSet(
            parameters = parameters,
            atoms = atoms,
            properties = properties,
        )

    def _read_previous(self, prev_dir: str | Path = None) -> tuple[Atoms, Dict[str, Any], Dict[str, Iterable[float]]]:
        """Read in previous results

        Parameters
        ----------
        prev_dir: str or Path
            The previous directory for the calculation
        """
        prev_atoms = None
        prev_parameters = {}
        prev_results = {}

        if (prev_dir):
            prev_parameters = json.load(
                open(f"{prev_dir}/parameters.json", "rt"), cls=MontyDecoder
            )
            try:
                prev_atoms = read_aims_output(f"{prev_dir}/aims.out")
                prev_results = prev_atoms.calc.results
            except IndexError, AimsParseError:
                pass

        return prev_atoms, prev_parameters, prev_results

    def _get_input_paramesters(self, prev_parameters: Dict[str, Any]=None) -> Dict[str, Any]:

        prev_parameters = {} if prev_parameters is None else prev_parameters
        parameters = dict(self.config_dict["aims_default_parameters"])

        # Generate base input but override with user input settings
        parameters = recursive_update(parameters, prev_parameters)
        parameters = recursive_update(parameters, self.user_parameters)

        return parameters
