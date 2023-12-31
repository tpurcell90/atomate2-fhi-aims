from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from atomate2.vasp.flows.core import DoubleRelaxMaker
from atomate2.vasp.jobs.core import DielectricMaker, StaticMaker, TightRelaxMaker
from atomate2.vasp.sets.core import StaticSetGenerator

from atomate2_temp.common.flows.phonons import BasePhononMaker
from atomate2_temp.vasp.jobs.phonons import PhononDisplacementMaker

if TYPE_CHECKING:
    from atomate2.vasp.jobs.base import BaseVaspMaker


@dataclass
class PhononMaker(BasePhononMaker):
    """
    Maker to calculate harmonic phonons with VASP and Phonopy.

    Overwrites the default Makers for the common PhononMaker

    Parameters
    ----------
    bulk_relax_maker : .BaseVaspMaker or None
        A maker to perform a tight relaxation on the bulk.
        Set to ``None`` to skip the
        bulk relaxation
    static_energy_maker : .BaseVaspMaker or None
        A maker to perform the computation of the DFT energy on the bulk.
        Set to ``None`` to skip the
        static energy computation
    born_maker: .BaseVaspMaker or None
        Maker to compute the BORN charges.
    phonon_displacement_maker : .BaseVaspMaker or None
        Maker used to compute the forces for a supercell.
    """

    code: str = "vasp"
    bulk_relax_maker: BaseVaspMaker | None = field(
        default_factory=lambda: DoubleRelaxMaker.from_relax_maker(TightRelaxMaker())
    )
    static_energy_maker: BaseVaspMaker | None = field(
        default_factory=lambda: StaticMaker(
            input_set_generator=StaticSetGenerator(auto_ispin=True)
        )
    )
    born_maker: BaseVaspMaker | None = field(default_factory=DielectricMaker)
    phonon_displacement_maker: BaseVaspMaker = field(
        default_factory=PhononDisplacementMaker
    )
