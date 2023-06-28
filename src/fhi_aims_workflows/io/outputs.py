"""A representation of FHI-aims output (based on ASE output parser)"""

from ase.io.aims import read_aims_output


class AimsOutput:
    """ The main output file for FHI-aims
    """

    def __init__(self, filename):
        """
        AimsOutput object constructor.

        Args:
            filename: (str) Name of the Aims output file to parse
        """
        with open(filename) as fd:
            output = read_aims_output(fd, index=slice(-1))

        print(output[0].calc.__dict__)
