"""A representation of FHI-aims output (based on ASE output parser)"""

from fhi_aims_workflows.io.parsers import read_aims_results
from monty import MSONable
from pathlib import Path
from typing import Dict, Any


class AimsOutputs(MSONable):
    """The main output file for FHI-aims"""

    def __init__(self, outfile: str | Path):
        """
        AimsOutput object constructor.

        Parameters
        ----------
        outfile
            The aims.out file to parse
        """
        self._results = read_aims_results(outfile, index=":")

    def as_dict(self):
        """Create a dict representation of the outputs for MSONable"""
        d = {"@module": self.__class__.__module__, "@class": self.__class__.__name__}

        d["results"] = self._results
        return d

    @classmethod
    def from_dict(self, d: Dict[str, Any]):
        """Constructor from a dictionary"""
        decoded = {
            k: MontyDecoder().process_decoded(v)
            for k, v in d.items()
            if not k.startswith("@")
        }
        self._results = decoded["results"]

    def get_results_for_image(self, image_ind: int | slice) -> Dict[str, Any]:
        """Get the results dictionary for a particular image or slice of images

        Parameters
        ----------
        image_ind
            The index of the images to get the results for

        Returns
        -------
        The results for those images
        """
        return self._results[image_ind]
