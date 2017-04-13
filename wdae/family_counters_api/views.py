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
                res[s['id']] = Counter()
            res[pedigree_selector['default']['id']] = Counter()

            for fid in family_ids:
                fam = dataset.families[fid]
                for p in fam.memberInOrder[2:]:
                    family_group = p.atts[pedigree_selector_id]
                    res[family_group]['all'] += 1
                    res[family_group][p.gender] += 1

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
