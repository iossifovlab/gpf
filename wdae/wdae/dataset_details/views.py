from rest_framework import status
from rest_framework.response import Response
from query_base.query_base import QueryBaseView
from rest_framework import permissions


class DatasetDetailsView(QueryBaseView):
    permission_classes = (permissions.IsAdminUser,)

    def get(self, request, dataset_id):
        if dataset_id is None:
            return Response({
                'error': 'No dataset ID given'
            }, status=status.HTTP_400_BAD_REQUEST)

        genotype_data = self.gpf_instance.get_genotype_data(dataset_id)

        if genotype_data is None:
            return Response({
                'error': f'No such dataset {dataset_id}'
            }, status=status.HTTP_400_BAD_REQUEST)

        dataset_details = \
            {'hasDenovo': genotype_data.has_denovo}
        return Response(dataset_details)
