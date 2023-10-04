"""Module defining core FHI-aims input set generators."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

from ase import Atoms

from atomate2_temp.aims.sets.base import AimsInputGenerator

__all__ = [
    "StaticSetGenerator",
    "RelaxSetGenerator",
]


@dataclass
class StaticSetGenerator(AimsInputGenerator):
    """Common class for ground-state generators."""

    calc_type: str = "static"

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
        return prev_parameters


@dataclass
class RelaxSetGenerator(AimsInputGenerator):
    """
    Class to generate FHI-aims relax sets.

    I.e., sets for optimization of internal and lattice coordinates.
    """

    calc_type: str = "relaxation"
    relax_cell: bool = True
    max_force: float = 1e-3
    method: str = "trm"

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
        updates = {"relax_geometry": f"{self.method} {self.max_force:e}"}
        if any(atoms.pbc) and self.relax_cell:
            updates["relax_unit_cell"] = "full"
        elif any(atoms.pbc):
            updates["relax_unit_cell"] = "none"

        return updates


@dataclass
class SocketIOSetGenerator(AimsInputGenerator):
    """Class to generate FHI-aims input sets for running with the socket"""

    calc_type: str = "multi_scf"
    host: str = "localhost"
    port: int = 12345

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
        updates = {"use_pimd_wrapper": (self.host, self.port)}

        return updates
