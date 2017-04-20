'''
Created on Apr 13, 2017

@author: lubo
'''
from rest_framework import status
from rest_framework.response import Response
from genotype_browser.views import QueryBaseView
from rest_framework.exceptions import NotAuthenticated
import traceback
import pprint
from collections import Counter


class FamilyCounters(QueryBaseView):
    """
Example:

        {
            "datasetId": "SSC",
            "pedigreeSelector": {
                "id": "phenotype",
                "checkedValues": ["autism", "unaffected"]
            },
            "effectTypes": ["Frame-shift", "Nonsense", "Splice-site"],
            "gender": ["female", "male"],
            "presentInChild": [
                "affected and unaffected",
                "affected only"
            ],
            "presentInParent": [
                "neither"
            ],
            "variantTypes": [
                "CNV", "del", "ins", "sub"
            ],
            "genes": "All",
            "phenoFilters": [
                {
                    "measureType": "continuous",
                    "measure":
                    "ssc_core_descriptive.ssc_diagnosis_nonverbal_iq",
                    "role": "prb",
                    "mmin": 80,
                    "mmax": 80
                }
            ]
        }

    """

    def __init__(self):
        super(FamilyCounters, self).__init__()

    def post(self, request):
        data = request.data
        try:
            dataset_id = data['datasetId']
            dataset = self.datasets_factory.get_dataset(dataset_id)
            self.check_object_permissions(request, dataset)

            family_ids = dataset.get_family_ids(**data)
            if family_ids is None:
                family_ids = dataset.families.keys()

            pedigree_selector = dataset.get_pedigree_selector(**data)
            pedigree_selector_id = pedigree_selector['id']

            pprint.pprint(pedigree_selector)
            res = {}
            for s in pedigree_selector['domain']:
                pprint.pprint(s)
                res[s['id']] = {
                    'count': Counter(),
                    'color': s['color'],
                    'name': s['name']
                }
            s = pedigree_selector['default']
            res[s['id']] = {
                'count': Counter(),
                'color': s['color'],
                'name': s['name']
            }

            for fid in family_ids:
                fam = dataset.families[fid]
                for p in fam.memberInOrder[2:]:
                    family_group = p.atts[pedigree_selector_id]
                    res[family_group]['count']['all'] += 1
                    res[family_group]['count'][p.gender] += 1

            res = [res[s['id']] for s in pedigree_selector['domain']]
            pprint.pprint(res)
            return Response(res, status=status.HTTP_200_OK)
        except NotAuthenticated:
            print("error while processing genotype query")
            traceback.print_exc()
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        except Exception:
            print("error while processing genotype query")
            traceback.print_exc()

            return Response(status=status.HTTP_400_BAD_REQUEST)
