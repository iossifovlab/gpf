# Create your views here.
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.decorators import api_view

from DAE import *


# class StudiesList(APIView):
#     """
#     List all studies.
#     """
#     base_name="studies"
#     
#     def get(self, request, format=None):
#         return Response(status=status.HTTP_204_NO_CONTENT)



@api_view(['GET'])
def denovo_studies_list(request):
    stds=vDB.getDenovoStudies()
    return Response({"denovo_studies":stds})

@api_view(['GET'])
def transmitted_studies_list(request):
    stds=vDB.getTransmittedStudies()
    return Response({"transmitted_studies":stds})


