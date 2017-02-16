'''
Created on Feb 16, 2017

@author: lubo
'''
from rest_framework import views, status
from rest_framework.response import Response
from gene.gene_set_collections import GeneSetsCollections


class GeneSetsCollectionsView(views.APIView):

    def __init__(self):

        self.gscs = GeneSetsCollections()

    def get(self, request):
        response = self.gscs.get_gene_sets_collections()
        return Response(response, status=status.HTTP_200_OK, )

