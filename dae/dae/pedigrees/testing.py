"""Defines tools usefull for testing families."""

import io
import textwrap

from dae.testing import convert_to_tab_separated

from dae.pedigrees.family import FamiliesData, Family
from dae.pedigrees.loader import FamiliesLoader


def build_families_data(content: str) -> FamiliesData:
    ped_content = io.StringIO(convert_to_tab_separated(
        textwrap.dedent(content)))
    return FamiliesLoader(ped_content).load()


def build_family(content: str) -> Family:
    families = build_families_data(content)
    return next(iter(families.values()))
