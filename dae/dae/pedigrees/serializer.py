import copy
from typing import List
from dae.pedigrees.family import FamiliesData, Family


class FamiliesTsvSerializer:
    """Class for serializing families into TSV format."""

    def __init__(self, families: FamiliesData):
        self._families = families

    def serialize(self, sep="\t", columns=None) -> List[str]:
        """Serialize families to list of lines with a header."""
        if columns is None:
            columns = list(self._families.values())[0].get_columns()
        rows = [f"{sep.join(columns)}\n"]
        for family in self._families.values():
            rows.extend(
                self._serialize_family(family, sep=sep, columns=columns)
            )
        return rows

    @staticmethod
    def _serialize_family(family: Family, sep="\t", columns=None) -> List[str]:
        """Serialize family to a list of lines per member."""
        if columns is None:
            columns = family.get_columns()
        rows = []
        for member in family.full_members:
            # pylint: disable=protected-access
            record = copy.deepcopy(member._attributes)
            record["mom_id"] = member.mom_id if member.mom_id else "0"
            record["dad_id"] = member.dad_id if member.dad_id else "0"
            record["generated"] = member.generated \
                if member.generated else False
            record["not_sequenced"] = member.not_sequenced \
                if member.not_sequenced else False
            row = []
            for col in columns:
                row.append(str(record.get(col, "-")))
            rows.append(f"{sep.join(row)}\n")
        return rows
