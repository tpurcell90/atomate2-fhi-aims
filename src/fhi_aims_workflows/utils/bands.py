"""Some utilities of dealing with bands. Copied from GIMS as of now; should be in its
own dedicated FHI-aims python package (with the parsers, plotters etc.)"""

from ase.dft.kpoints import resolve_kpt_path_string, kpoint_convert
import numpy as np

# TODO add the same procedures but using pymatgen routines


def prepare_band_input(cell, density=20):
    """
    Prepares the band information needed for the FHI-aims control.in file.

    Parameters:

    cell: object
        ASE cell object
    density: int
        Number of kpoints per Angstrom. Default: 20
    """
    bp = cell.bandpath()
    # print(cell.get_bravais_lattice())
    r_kpts = resolve_kpt_path_string(bp.path, bp.special_points)

    lines_and_labels = []
    for labels, coords in zip(*r_kpts):
        dists = coords[1:] - coords[:-1]
        lengths = [np.linalg.norm(d) for d in kpoint_convert(cell, skpts_kc=dists)]
        points = np.int_(np.round(np.asarray(lengths) * density))
        # I store it here for now. Might be needed to get global info.
        lines_and_labels.append(
            [points, labels[:-1], labels[1:], coords[:-1], coords[1:]]
        )

    bands = []
    for segment in lines_and_labels:
        for points, lstart, lend, start, end in zip(*segment):
            bands.append(
                "band {:9.5f}{:9.5f}{:9.5f} {:9.5f}{:9.5f}{:9.5f} {:4} {:3}{:3}".format(
                    *start, *end, points, lstart, lend
                )
            )

    return bands