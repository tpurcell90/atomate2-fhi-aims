from ase.atoms import Atoms
from monty.json import MSONable, MontyDecoder


class MSONableAtoms(Atoms, MSONable):
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

        return cls.fromdict(decoded)
