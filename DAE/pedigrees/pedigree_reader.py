import csv
from collections import OrderedDict
from pedigrees import Pedigree, PedigreeMember


class PedigreeReader(object):

    def read_file(self, filename, return_as_dict=False):
        families = OrderedDict()
        with open(filename, 'r') as file:
            reader = csv.DictReader(file, delimiter='\t')

            for row in reader:
                kwargs = {
                    "family_id": row["familyId"],
                    "id": row["personId"],
                    "father": row["dadId"],
                    "mother": row["momId"],
                    "sex": row["sex"],
                    "label": "",
                    "effect": row["status"],
                }
                member = PedigreeMember(**kwargs)
                if member.family_id not in families:
                    families[member.family_id] = Pedigree([member])
                else:
                    families[member.family_id].add_member(member)

        if return_as_dict:
            return families
        return families.values()
