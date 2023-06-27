from ase.atoms import Atoms
from monty.json import MSONable, MontyDecoder


class MSONableAtoms(Atoms, MSONable):
    def __init__(
        self,
        symbols=None,
        positions=None,
        numbers=None,
        tags=None,
        momenta=None,
        masses=None,
        magmoms=None,
        charges=None,
        scaled_positions=None,
        cell=None,
        pbc=None,
        celldisp=None,
        constraint=None,
        calculator=None,
        info=None,
        velocities=None,
    ):
        super().__init__(
            symbols,
            positions,
            numbers,
            tags,
            momenta,
            masses,
            magmoms,
            charges,
            scaled_positions,
            cell,
            pbc,
            celldisp,
            constraint,
            calculator,
            info,
            velocities,
        )

    def as_dict(self):
        d = {"@module": self.__class__.__module__, "@class": self.__class__.__name__}

        for key, val in self.todict().items():
            d[key] = val

        return d

    @classmethod
    def from_dict(cls, d):
        decoded = {
            k: MontyDecoder().process_decoded(v)
            for k, v in d.items()
            if not k.startswith("@")
        }

        return super().fromdict(decoded)
