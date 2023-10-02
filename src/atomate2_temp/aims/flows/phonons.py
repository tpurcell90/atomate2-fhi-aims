from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from atomate2_temp.common.flows.phonons import BasePhononMaker

from atomate2_temp.aims.flows.core import DoubleRelaxMaker
from atomate2_temp.aims.jobs.base import BaseAimsMaker
from atomate2_temp.aims.jobs.core import StaticMaker
from atomate2_temp.aims.jobs.phonons import (
    PhononDisplacementMaker,
    PhononDisplacementMakerSocket,
)

if TYPE_CHECKING:
    from atomate2_temp.aims.jobs.base import BaseAimsMaker


@dataclass
class PhononMaker(BasePhononMaker):
    """
    Maker to calculate harmonic phonons with VASP and Phonopy.

    Overwrites the default Makers for the common PhononMaker

    Parameters
    ----------
    bulk_relax_maker : .BaseAimsMaker or None
        A maker to perform a tight relaxation on the bulk.
        Set to ``None`` to skip the
        bulk relaxation
    static_energy_maker : .BaseAimsMaker or None
        A maker to perform the computation of the DFT energy on the bulk.
        Set to ``None`` to skip the
        static energy computation
    born_maker: .BaseAimsMaker or None
        Maker to compute the BORN charges.
    phonon_displacement_maker : .BaseAimsMaker or None
        Maker used to compute the forces for a supercell.
    """

    code: str = "aims"
    bulk_relax_maker: BaseAimsMaker | None = field(
        default_factory=lambda: DoubleRelaxMaker.from_parmeters(dict())
    )
    static_energy_maker: BaseAimsMaker | None = field(default_factory=StaticMaker)
    born_maker: BaseAimsMaker | None = None
    phonon_displacement_maker: BaseAimsMaker | None = None

    def __post_init__(self):
        if self.phonon_displacement_maker is None:
            if self.socket:
                self.phonon_displacement_maker = PhononDisplacementMakerSocket()
            else:
                self.phonon_displacement_maker = PhononDisplacementMaker()
