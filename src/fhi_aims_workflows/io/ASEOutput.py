from monty.json import MSONable, MontyDecoder
from fhi_aims_workflows.utils.MSONableAtoms import MSONableAtoms


class ASEOutputs(MSONable):
    def __init__(self, atoms: MSONableAtoms):
        """ASEOutputs object used for pymatgen conversion

        Parameters
        ----------
        atoms: MSONableAtoms
            The atoms object from the calculation
        """
        if atoms.calc:
            self._results = atoms.calc.results
        else:
            self._results = {}

        self._atoms = atoms

    @property
    def atoms(self):
        return self._atoms

    @property
    def results(self):
        return self._results

    def get_property(self, key):
        return self._results.get(key, None)

    @property
    def energy(self):
        return self._results.get("energy", None)

    @property
    def forces(self):
        return self._results.get("forces", None)

    @property
    def stress(self):
        return self._results.get("stress", None)

    @property
    def stresses(self):
        return self._results.get("stresses", None)

    @property
    def dipole(self):
        return self._results.get("dipole", None)

    @property
    def charges(self):
        return self._results.get("charges", None)

    @property
    def magmom(self):
        return self._results.get("magmom", None)

    @property
    def magmoms(self):
        return self._results.get("magmoms", None)

    @property
    def free_energy(self):
        return self._results.get("free_energy", None)

    @property
    def energies(self):
        return self._results.get("energies", None)

    @property
    def dielectric_tensor(self):
        return self._results.get("dielectric_tensor", None)

    @property
    def born_effective_charges(self):
        return self._results.get("born_effective_charges", None)

    @property
    def polarization(self):
        return self._results.get("polarization", None)

    def as_dict(self):
        d = {
            "@module": self.__class__.__module__,
            "@class": self.__class__.__name__,
            "atoms": self._atoms,
            "results": self._results,
        }

        return d

    @classmethod
    def from_dict(cls, d):
        decoded = {
            k: MontyDecoder().process_decoded(v)
            for k, v in d.items()
            if not k.startswith("@")
        }

        results = decoded.pop("results")
        atoms = Atoms.fromdict(decoded["atoms"])

        calculator = SinglePointDFTCalculator(atoms)
        calculator.results = results

        atoms.calc = calculator

        return cls(atoms)
