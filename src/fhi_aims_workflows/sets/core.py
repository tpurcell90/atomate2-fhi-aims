"""Module defining core FHI-aims input set generators."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

import numpy as np

from fhi_aims_workflows.sets.base import AimsInputGenerator

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
        return {}


@dataclass
class RelaxSetGenerator(AimsInputGenerator):
    """
    Class to generate CP2K relax sets.

    I.e., sets for optimization of internal coordinates without cell parameter
    optimization.
    """

    calc_type: str = "relaxation"

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
        updates = {
            "relax_geometry": "trm 1e-3",
        }
        if any(atoms.pbc):
            updates["relax_unit_cell"] = "full"
        return updates
