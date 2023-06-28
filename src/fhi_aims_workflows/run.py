"""An FHI-aims jobflow runner"""
from __future__ import annotations

import logging
import os
from os.path import expandvars
import subprocess

from fhi_aims_workflows.schemas.task import TaskDocument

# from typing import Dict, Any

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
    aims_cmd = aims_cmd or os.getenv('ASE_AIMS_COMMAND')
    if not aims_cmd:
        raise RuntimeError('No aims.x command found')
    # aims_job_kwargs = aims_job_kwargs or {}

    aims_cmd = expandvars(aims_cmd)

    logger.info(f"Running command: {aims_cmd}")
    return_code = subprocess.call(aims_cmd, shell=True)
    logger.info(f"{aims_cmd} finished running with return code: {return_code}")


def should_stop_children(
    task_document: TaskDocument,
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
        raise RuntimeError(
            "Job was not successful (not converged)!"
        )

    raise RuntimeError(f"Unknown option for handle_unsuccessful: {handle_unsuccessful}")
