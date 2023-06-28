"""A representation of FHI-aims output (based on ASE output parser)"""
from fhi_aims_workflows.io.parsers import read_aims_output, read_aims_header_info
from monty.json import MSONable, MontyDecoder
from pathlib import Path
from typing import Dict, Any


class AimsOutput(MSONable):
    """The main output file for FHI-aims"""

    def __init__(self, results, metadata, atoms_summary):
        """AimsOutput object constructor

        Parameters
        ----------
        results
            A list of all images in an output file
        metadata
            The metadata of the executable used to preform the calculation
        atoms_summary
            The summary of the starting atomic structure
        """
        self._results = results
        self._metadata = metadata
        self._atoms_summary = atoms_summary

    def as_dict(self):
        """Create a dict representation of the outputs for MSONable"""
        d = {"@module": self.__class__.__module__, "@class": self.__class__.__name__}

        d["results"] = self._results
        d["metadata"] = self._metadata
        d["atoms_summary"] = self._atoms_summary
        return d

    @classmethod
    def from_outfile(cls, outfile: str | Path):
        """
        AimsOutput object constructor.

        Parameters
        ----------
        outfile
            The aims.out file to parse
        """
        metadata, atoms_summary = read_aims_header_info(outfile)
        results = read_aims_output(outfile, index=slice(-1))

        return cls(results, metadata, atoms_summary)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]):
        """Constructor from a dictionary"""
        decoded = {
            k: MontyDecoder().process_decoded(v)
            for k, v in d.items()
            if not k.startswith("@")
        }
        return cls(decoded["results"], decoded["metadata"], decoded["atoms_summary"])

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

    @property
    def atoms_summary(self):
        """The summary of the material/molecule that the calculations represent"""
        return self._atoms_summary

    @property
    def metadata(self):
        """The system metadata"""
        return self._metadata

    @property
    def n_images(self):
        """The number of images in results"""
        return len(self._results)
