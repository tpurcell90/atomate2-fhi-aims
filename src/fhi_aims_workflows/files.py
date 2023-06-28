"""Functions dealing with FHI-aims files"""
from __future__ import annotations

import logging
from glob import glob
from pathlib import Path

from atomate2.common.files import get_zfile, copy_files, gunzip_files
from atomate2.utils.file_client import auto_fileclient, FileClient
from atomate2.utils.path import strip_hostname

logger = logging.getLogger(__name__)

__all__ = [
    "copy_aims_outputs",
]


@auto_fileclient
def copy_aims_outputs(
    src_dir: Path | str,
    src_host: str | None = None,
    additional_aims_files: list[str] | None = None,
    restart_to_input: bool = True,
    file_client: FileClient | None = None,
):
    """
    Copy FHI-aims output files to the current directory (inspired by CP2K plugin).

    Parameters
    ----------
    src_dir : str or Path
        The source directory.
    src_host : str or None
        The source hostname used to specify a remote filesystem. Can be given as
        either "username@remote_host" or just "remote_host" in which case the username
        will be inferred from the current user. If ``None``, the local filesystem will
        be used as the source.
    additional_aims_files : list of str
        Additional files to copy
    restart_to_input : bool
        Move the aims restart files to by the aims input in the new directory
    file_client : .FileClient
        A file client to use for performing file operations.
    """
    src_dir = strip_hostname(src_dir)
    logger.info(f"Copying FHI-aims inputs from {src_dir}")
    directory_listing = file_client.listdir(src_dir, host=src_host)
    # additional files like bands, DOS, *.cube, whatever
    additional_files = additional_aims_files if additional_aims_files else []

    if restart_to_input:
        additional_files += ("hessian.aims", "geometry.in.next_step", "*.csc")

    # copy files
    files = ["aims.out"]

    for pattern in set(additional_files):
        for f in (glob((Path(src_dir) / pattern).as_posix())):
            files.append(Path(f).name)

    all_files = [
        get_zfile(directory_listing, r, allow_missing=True) for r in files
    ]
    all_files = [f for f in all_files if f]

    copy_files(
        src_dir,
        src_host=src_host,
        include_files=all_files,
        file_client=file_client,
    )

    gunzip_files(
        include_files=all_files,
        allow_missing=True,
        file_client=file_client,
    )

    logger.info("Finished copying inputs")
