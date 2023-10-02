from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from monty.json import MSONable


@dataclass
class DataFile(MSONable):
    """A data file for a cp2k calc."""

    objects: Sequence | None = None

    # TARP: Do these classmethods do anything?
    @classmethod
    def from_file(cls, fn):
        """Load from a file"""
        with open(fn) as f:
            data = cls.from_string(f.read())
            for obj in data.objects:
                obj.filename = fn
            return data

    @classmethod
    def from_string(cls, s):
        """Initialize from a string"""
        raise NotImplementedError

    def write_file(self, fn):
        """Write to a file"""
        with open(fn, "w") as f:
            f.write(self.get_string())

    def get_string(self):
        """Get string representation"""
        return "\n".join(b.get_string() for b in self.objects)

    def __str__(self):
        return self.get_string()
