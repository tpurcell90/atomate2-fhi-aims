from ase.atoms import Atoms
from ase.calculators.singlepoint import SinglePointDFTCalculator

import numpy as np

from monty.json import MSONable, MontyDecoder

from pymatgen.core import Structure, Molecule
from pymatgen.io.ase import AseAtomsAdaptor

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

    @classmethod
    def from_pymatgen(cls, structure: Structure | Molecule):
        return ASE_ADAPTOR.get_atoms(structure)

    @property
    def structure(self):
        return ASE_ADAPTOR.get_structure(self)

    @property
    def pymatgen(self):
        if np.any(self.pbc):
            return ASE_ADAPTOR.get_structure(self)

        return ASE_ADAPTOR.get_molecule(self)
