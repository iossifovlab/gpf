'''
Created on Feb 6, 2017

@author: lubo
'''
from rest_framework import views, status
from rest_framework.response import Response
from users.authentication import SessionAuthenticationWithoutCSRF
from rest_framework import permissions

from helpers.logger import log_filter, LOGGER
import traceback
import preloaded
from rest_framework.exceptions import NotAuthenticated


class IsDatasetAllowed(permissions.BasePermission):

    def has_object_permission(self, request, view, dataset):
        user = request.user

        print("has_object_permission", dataset.descriptor[
              'visibility'], user.is_authenticated())

        access_rights = False
        if dataset.descriptor['visibility'] == 'ALL':
            access_rights = True
        if dataset.descriptor['visibility'] == 'AUTHENTICATED' \
                and user.is_authenticated():
            access_rights = True
        if dataset.descriptor['visibility'] == 'STAFF' \
                and user.is_staff:
            access_rights = True

        return access_rights


class QueryPreviewView(views.APIView):
    authentication_classes = (SessionAuthenticationWithoutCSRF, )
    permission_classes = (IsDatasetAllowed,)

    def __init__(self):
        register = preloaded.register.get_register()
        self.datasets = register.get('datasets')
        assert self.datasets is not None

        self.datasets_config = self.datasets.get_config()
        self.datasets_factory = self.datasets.get_factory()

    def prepare_variants_resonse(self, variants):
        rows = []
        cols = variants.next()
        count = 0
        for v in variants:
            count += 1
            if count <= 1000:
                rows.append(v)
            if count > 2000:
                break
        if count <= 2000:
            count = str(count)
        else:
            count = 'more than 2000'

        return {
            'count': count,
            'cols': cols,
            'rows': rows
        }

    def prepare_legend_response(self, dataset, **data):
        legend = dataset.get_pedigree_selector(**data)
        response = legend.domain[:]
        response.append(legend.default)
        return response

    def post(self, request):
        LOGGER.info(log_filter(request, "query v3 preview request: " +
                               str(request.data)))

        data = request.data
        try:
            dataset_id = data['datasetId']
            dataset = self.datasets_factory.get_dataset(dataset_id)
            self.check_object_permissions(request, dataset)

            legend = self.prepare_legend_response(dataset)
            variants = dataset.get_variants_preview(
                safe=True,
                **data)
            res = self.prepare_variants_resonse(variants)

            res['legend'] = legend

            return Response(res, status=status.HTTP_200_OK)
        except NotAuthenticated:
            print("error while processing genotype query")
            traceback.print_exc()
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        except Exception:
            print("error while processing genotype query")
            traceback.print_exc()

            return Response(status=status.HTTP_400_BAD_REQUEST)
