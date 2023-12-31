from phonopy.units import VaspToTHz

from atomate2_temp.aims.utils.units import omega_to_THz


def get_factor(code: str):
    """
    Get the frequency conversion factor to THz for each code

    Parameters
    ----------
    code: str
        The code to get the conversion factor for

    Returns
    -------
    float
        The correct conversion factor

    Raises
    ------
    ValueError
        If code is not defined
    """
    if code == "vasp":
        return VaspToTHz
    elif code == "aims":
        return omega_to_THz  # Based on CODATA 2002
    else:
        raise ValueError(f"Frequency conversion factor for code ({code}) not defined.")
