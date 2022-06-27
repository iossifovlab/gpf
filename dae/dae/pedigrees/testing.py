"""Defines tools usefull for testing families."""

import io
import textwrap
from typing import cast

from dae.genomic_resources.test_tools import convert_to_tab_separated

from dae.pedigrees.family import Family
from dae.pedigrees.loader import FamiliesLoader


def build_family(content: str) -> Family:
    ped_content = io.StringIO(convert_to_tab_separated(
        textwrap.dedent(content)))
    families = FamiliesLoader(ped_content).load()
    return cast(Family, next(iter(families.values())))
