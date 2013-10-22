# Create your views here.
from rest_framework.response import Response
from rest_framework.decorators import api_view

from DAE import *


@api_view(['GET'])
def denovo_studies_list(request):
    stds=vDB.getDenovoStudies()
    return Response({"denovo_studies" : stds})

@api_view(['GET'])
def study_groups_list(request):
    stds=vDB.getStudyGroups()
    return Response({"study_groups" : stds})


@api_view(['GET'])
def transmitted_studies_list(request):
    stds=vDB.getTransmittedStudies()
    return Response({"transmitted_studies" : stds})


@api_view(['GET'])
def effect_types_list(request):
    eff=vDB.get_effect_types()
    return Response({"effect_types" : eff})

@api_view(['GET'])
def variant_types_list(request):
    var_types=vDB.get_variant_types()
    return Response({'variant_types': var_types})

@api_view(['GET'])
def child_type_list(request):
    child_types=vDB.get_child_types()
    return Response({'child_types':child_types})

@api_view(['GET'])
def families_list(request,study_name=None):

    st=vDB.get_study(study_name)
    families=st.families
    
    query_params=request.QUERY_PARAMS
    print query_params
    if query_params.has_key('filter'):
        start_string=query_params['filter']
        families=[f for f in families if f.startswith(start_string)]
        
    return Response({'study':study_name,
                     'families':families})

    
