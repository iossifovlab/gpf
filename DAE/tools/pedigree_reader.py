import csv
from collections import OrderedDict
from pedigrees import Pedigree, PedigreeMember


class PedigreeReader(object):

    def read_file(self, file, columns_labels, header=None, delimiter='\t',
                  return_as_dict=False):
        families = OrderedDict()
        with open(file) as csvfile:
            reader = csv.DictReader(csvfile, fieldnames=header,
                                    delimiter=delimiter)
            for row in reader:
                kwargs = {
                    "family_id": row[columns_labels["family_id"]],
                    "id": row[columns_labels["id"]],
                    "father": row[columns_labels["father"]],
                    "mother": row[columns_labels["mother"]],
                    "sex": row[columns_labels["sex"]],
                    "effect": row[columns_labels["effect"]],
                    "layout": row.get(columns_labels["layout"], None)
                }
                member = PedigreeMember(**kwargs)
                if member.family_id not in families:
                    families[member.family_id] = Pedigree([member])
                else:
                    families[member.family_id].members.append(member)

        if return_as_dict:
            return families
        return list(families.values())
