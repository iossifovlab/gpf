import csv
from collections import OrderedDict
from dae.pedigrees.pedigrees import Pedigree, PedigreeMember


class PedigreeReader(object):

    def read_file(self, file, columns_labels=None, header=None, delimiter='\t',
                  return_as_dict=False):
        if columns_labels is None:
            columns_labels = PedigreeReader.get_default_colum_labels()
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
                    "status": row[columns_labels["status"]],
                    "role": row[columns_labels["role"]],
                    "layout": row.get(columns_labels["layout"], None)
                }
                if 'generated' in columns_labels:
                    generated = row.get(columns_labels["generated"], False)
                    kwargs["generated"] = True if generated else False
                member = PedigreeMember(**kwargs)
                if member.family_id not in families:
                    families[member.family_id] = Pedigree([member])
                else:
                    families[member.family_id].members.append(member)

        if return_as_dict:
            return families
        return list(families.values())

    @staticmethod
    def get_default_colum_labels():
        return {
            "family_id": "familyId",
            "id": "personId",
            "father": "dadId",
            "mother": "momId",
            "sex": "gender",
            "status": "status",
            "role": "role",
            "layout": "layout"
        }
