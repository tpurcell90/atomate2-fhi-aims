"""Module with common file names and classes used for Abinit flows."""

import logging
import os
import contextlib

TMPDIR_NAME = "tmpdir"
OUTDIR_NAME = "outdata"
INDIR_NAME = "indata"
TMPDATAFILE_PREFIX = "tmp"
OUTDATAFILE_SUFFIX = "out"
INDATAFILE_SUFFIX = "in"
TMPDATA_PREFIX = os.path.join(TMPDIR_NAME, TMPDATAFILE_PREFIX)
OUTDATA_PREFIX = os.path.join(OUTDIR_NAME, OUTDATAFILE_PREFIX)
INDATA_PREFIX = os.path.join(INDIR_NAME, INDATAFILE_PREFIX)
STDERR_FILE_NAME = "run.err"
LOG_FILE_NAME = "run.log"
OUTPUT_FILE_NAME: str = "aims.out"
CONTROL_FILE_NAME: str = "control.in"
PARAMS_JSON_FILE_NAME: str = "parameters.json"
GEOMETRY_FILE_NAME: str = "geometry.in"
MPIABORTFILE = "__AIMS_MPIABORTFILE__"
DUMMY_FILENAME = "__DUMMY__"


@contextlib.contextmanager
def cwd(path, mkdir=False, debug=False):
    """Change cwd intermediately

    Example
    -------
    >>> with cwd(some_path):
    >>>     do so some stuff in some_path
    >>> do so some other stuff in old cwd

    Parameters
    ----------
    path: str or Path
        Path to change working directory to
    mkdir: bool
        If True make path if it does not exist
    debug: bool
        If True enter debug mode
    """
    CWD = os.getcwd()

    if os.path.exists(path) is False and mkdir:
        os.makedirs(path)

    if debug:
        os.chdir(path)
        yield
        os.chdir(CWD)
        return

    os.chdir(path)
    yield
    os.chdir(CWD)
