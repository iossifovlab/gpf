'''
Created on Apr 13, 2017

@author: lubo
'''
from rest_framework import status
from rest_framework.response import Response
from genotype_browser.views import QueryBaseView
from rest_framework.exceptions import NotAuthenticated
import traceback
import logging

LOGGER = logging.getLogger(__name__)


class FamilyCounters(QueryBaseView):
    """
Example:

        {
            "datasetId": "SSC",
            "peopleGroup": {
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
        # FIXME:
        # It uses old interface
        return Response([], status=status.HTTP_200_OK)
        data = request.data
        try:
            dataset_id = data['datasetId']
            dataset = self.get_dataset(dataset_id)
            self.check_object_permissions(request, dataset_id)

            family_ids = dataset.get_family_ids(**data)
            if family_ids is None:
                family_ids = list(dataset.families.keys())

            people_group = dataset.get_people_group(**data)
            people_group_id = people_group['id']

            res = {}
            for s in people_group['domain']:
                res[s['id']] = {
                    'count': {'M': 0, 'F': 0, 'all': 0},
                    'color': s['color'],
                    'name': s['name']
                }
            s = people_group['default']
            res[s['id']] = {
                'count': {'M': 0, 'F': 0, 'all': 0},
                'color': s['color'],
                'name': s['name']
            }

            for fid in family_ids:
                fam = dataset.families.get(fid, None)
                if fam is None:
                    continue
                for p in fam.memberInOrder[2:]:
                    family_group = p.atts[people_group_id]
                    res[family_group]['count']['all'] += 1
                    res[family_group]['count'][p.gender.name] += 1

            res = [res[s['id']] for s in people_group['domain']]
            return Response(res, status=status.HTTP_200_OK)
        except NotAuthenticated:
            LOGGER.exception("error while processing genotype query")
            traceback.print_exc()
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        except Exception:
            LOGGER.exception("error while processing genotype query")
            traceback.print_exc()

            return Response(status=status.HTTP_400_BAD_REQUEST)
