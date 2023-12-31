from dataclasses import dataclass, field

from atomate2_temp.aims.jobs.base import BaseAimsMaker
from atomate2_temp.aims.jobs.core import SocketIOStaticMaker
from atomate2_temp.aims.sets.base import AimsInputGenerator
from atomate2_temp.aims.sets.core import SocketIOSetGenerator, StaticSetGenerator


@dataclass
class PhononDisplacementMaker(BaseAimsMaker):
    """
    Maker to perform a static calculation as a part of the finite displacement method.

    The input set is for a static run with tighter convergence parameters.
    Both the k-point mesh density and convergence parameters
    are stricter than a normal relaxation.

    Parameters
    ----------
    name: str
        The job name.
    input_set_generator: AimsInputGenerator
        A generator used to make the input set.
    """

    name: str = "phonon static aims"

    input_set_generator: AimsInputGenerator = field(
        default_factory=lambda: StaticSetGenerator(
            user_parameters={"compute_forces": True},
            user_kpoints_settings={"density": 5.0, "even": True},
        )
    )


@dataclass
class PhononDisplacementMakerSocket(SocketIOStaticMaker):
    """
    Maker to perform a static calculation as a part of the finite displacement method.

    The input set is for a static run with tighter convergence parameters.
    Both the k-point mesh density and convergence parameters
    are stricter than a normal relaxation.

    Parameters
    ----------
    name: str
        The job name.
    input_set_generator: AimsInputGenerator
        A generator used to make the input set.
    """

    name: str = "phonon static aims socket"

    input_set_generator: AimsInputGenerator = field(
        default_factory=lambda: SocketIOSetGenerator(
            user_parameters={"compute_forces": True},
            user_kpoints_settings={"density": 5.0, "even": True},
        )
    )
