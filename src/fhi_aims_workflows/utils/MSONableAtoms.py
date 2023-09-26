from ase.atoms import Atoms
from ase.calculators.singlepoint import SinglePointDFTCalculator
from pymatgen.io.ase import AseAtomsAdaptor

from monty.json import MSONable, MontyDecoder

ASE_ADAPTOR = AseAtomsAdaptor()


class MSONableAtoms(Atoms, MSONable):
    def as_dict(self):
        d = {"@module": self.__class__.__module__, "@class": self.__class__.__name__}

        for key, val in self.todict().items():
            d[key] = val

        if self.calc:
            d["calculated_results"] = self.calc.results

        return d

    @classmethod
    def from_dict(cls, d):
        decoded = {
            k: MontyDecoder().process_decoded(v)
            for k, v in d.items()
            if not k.startswith("@")
        }
        calculated_results = decoded.pop("calculated_results", None)

        atoms = Atoms.fromdict(decoded)

        calculator = SinglePointDFTCalculator(atoms)
        calculator.results = calculated_results

        return cls(atoms, calculator=calculator)

    @property
    def pymatgen_pair(self):
        if np.any(self.pbc):
            structure = ASE_ADAPTOR.get_structure(self)
            molecule = None
        else:
            structure = None
            molecule = ASE_ADAPTOR.get_molecule(self)

        return (structure, molecule)
