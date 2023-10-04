"""An FHI-aims jobflow runner"""
from __future__ import annotations

import json
import logging
import os
import subprocess
from os.path import expandvars
from typing import Iterable

from ase.calculators.aims import Aims
from ase.calculators.socketio import SocketIOCalculator
from monty.json import MontyDecoder

from atomate2_temp.aims.schemas.task import AimsTaskDocument
from atomate2_temp.aims.utils.MSONableAtoms import MSONableAtoms

logger = logging.getLogger(__name__)


def run_aims(
    aims_cmd: str = None,
    # aims_job_kwargs: Dict[str, Any] = None,
):
    """
    Run FHI-aims.

    Parameters
    ----------
    aims_cmd : str
        The command used to run FHI-aims (defaults to ASE_AIMS_COMMAND env variable).
    # aims_job_kwargs : dict
    #     Keyword arguments that are passed to :obj:`.AimsJob`.
    """
    aims_cmd = aims_cmd or os.getenv("ASE_AIMS_COMMAND")
    if not aims_cmd:
        raise RuntimeError("No aims.x command found")
    # aims_job_kwargs = aims_job_kwargs or {}

    aims_cmd = expandvars(aims_cmd)

    logger.info(f"Running command: {aims_cmd}")
    return_code = subprocess.call(["/bin/bash", "-c", aims_cmd], env=os.environ)
    logger.info(f"{aims_cmd} finished running with return code: {return_code}")


def should_stop_children(
    task_document: AimsTaskDocument,
    handle_unsuccessful: bool | str = True,
) -> bool:
    """
    Decide whether child jobs should continue.

    Parameters
    ----------
    task_document : .TaskDocument
        An FHI-aims task document.
    handle_unsuccessful : bool or str
        This is a three-way toggle on what to do if your job looks OK, but is actually
        not converged (either electronic or ionic):

        - `True`: Mark job as completed, but stop children.
        - `False`: Do nothing, continue with workflow as normal.
        - `"error"`: Throw an error.

    Returns
    -------
    bool
        Whether to stop child jobs.
    """
    if task_document.state == "successful":
        return False

    if isinstance(handle_unsuccessful, bool):
        return handle_unsuccessful

    if handle_unsuccessful == "error":
        raise RuntimeError("Job was not successful (not converged)!")

    raise RuntimeError(f"Unknown option for handle_unsuccessful: {handle_unsuccessful}")


def run_aims_socket(atoms_to_calculate: Iterable[MSONableAtoms], aims_cmd: str = None):
    """Uses the ASE interface to run FHI-aims from the socket

    Parameters
    ----------
    atoms_to_calculate
        The list of structures to run scf calculations on
    aims_cmd:
        The aims command to use
    """

    parameters = json.load(open("parameters.json", "rt"), cls=MontyDecoder)
    if aims_cmd:
        parameters["aims_command"] = aims_cmd
    elif "aims_command" not in parameters:
        aims_cmd = os.getenv("ASE_AIMS_COMMAND")

    calculator = Aims(**parameters)
    port = parameters["use_pimd_wrapper"][1]
    atoms = atoms_to_calculate[0].copy()

    with calculator.socketio(port=port) as calc:
        for atoms_calc in atoms_to_calculate:
            # Delete prior calculation results
            calc.results.clear()

            # Reset atoms information to the new cell
            atoms.info = atoms_calc.info
            atoms.cell = atoms_calc.cell
            atoms.positions = atoms_calc.positions

            calc.calculate(atoms, system_changes=["positions", "cell"])

        calc.close()
