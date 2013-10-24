# Create your views here.
from django.http import HttpResponse
from django.conf import settings
  

from rest_framework.response import Response
from rest_framework.decorators import api_view

from rest_framework import status

from DAE import vDB, giDB, get_gene_sets_symNS,_safeVs

from GetVariantsInterface import augmentAVar

import itertools

__add_headers={'Access-Control-Allow-Origin':'*'}

@api_view(['GET'])
def denovo_studies_list(request):
    stds=vDB.getDenovoStudies()
    return Response({"denovo_studies" : stds},headers=__add_headers)

@api_view(['GET'])
def study_groups_list(request):
    stds=vDB.getStudyGroups()
    return Response({"study_groups" : stds},headers=__add_headers)


@api_view(['GET'])
def transmitted_studies_list(request):
    stds=vDB.getTransmittedStudies()
    return Response({"transmitted_studies" : stds},headers=__add_headers)


@api_view(['GET'])
def effect_types_list(request):
    eff=vDB.get_effect_types()
    return Response({"effect_types" : eff},headers=__add_headers)

@api_view(['GET'])
def variant_types_list(request):
    var_types=vDB.get_variant_types()
    return Response({'variant_types': var_types},headers=__add_headers)

@api_view(['GET'])
def child_type_list(request):
    child_types=vDB.get_child_types()
    return Response({'child_types':child_types},headers=__add_headers)

@api_view(['GET'])
def families_list(request,study_name=None):

    st=vDB.get_study(study_name)
    families=st.families.keys()
    
    query_params=request.QUERY_PARAMS
    if query_params.has_key('filter'):
        start_string=query_params['filter']
        families=[f for f in families if f.startswith(start_string)]
        
    return Response({'study':study_name,
                     'families':families},headers=__add_headers)

@api_view(['GET'])
def gene_set_denovo_list(request,denovo_study):
    try:
        gts = vDB.get_denovo_sets(str(denovo_study))
        return Response(gts.tDesc,headers=__add_headers) 
    
    except Exception as e:
        print "Exception: ",e
        return Response(status=status.HTTP_404_NOT_FOUND,data={"reason":"Denovo study <%s> not found..."%denovo_study},headers=__add_headers)
        
def __get_page_count(query_params, page_count=30):
    if query_params.has_key('page_count'):
        try:
            page_count = int(query_params['page_count'])
        except:
            page_count = 30
    if not (page_count > 0 and page_count <= 100):
        page_count = 30
    return page_count

def __gene_set_filter_response_dict(request,data):
    query_params=request.QUERY_PARAMS
    
    page_count=__get_page_count(query_params,page_count=100)
    print "page_count:", page_count
    
    if query_params.has_key('filter'):
        filter_string=query_params['filter']
        l=[(key,value) for (key,value) in data.items() if (filter_string in key) or (filter_string in value)]
        return dict(l[0:page_count])
    else:
        return dict(data.items()[0:page_count])

@api_view(['GET'])
def gene_set_main_list(request):
    gts = settings.GENE_SETS_MAIN
    res=__gene_set_filter_response_dict(request, gts.tDesc)
    return Response(res,headers=__add_headers) 
    
        
@api_view(['GET'])
def gene_set_go_list(request):
    gts=settings.GENE_SETS_GO
    res=__gene_set_filter_response_dict(request, gts.tDesc)
    return Response(res,headers=__add_headers)

@api_view(['GET'])
def gene_set_disease_list(request):
    gts=settings.GENE_SETS_DISEASE
    res=__gene_set_filter_response_dict(request, gts.tDesc)
    return Response(res,headers=__add_headers)


@api_view(['GET'])
def gene_list(request,page_count=30):
    gl=[g.sym for g in giDB.genes.values()]

    query_params=request.QUERY_PARAMS
    
    if query_params.has_key('filter'):
        start_string=query_params['filter']
        gl=[g for g in gl if g.startswith(start_string)]
        
    page_count = __get_page_count(query_params, page_count)
        
    return Response(gl[:page_count],headers=__add_headers)




@api_view(['POST'])
def get_variants_csv(request):
    data=request.DATA
    print data
    
    dvs = []
    if data.has_key('denovoStudies'):
        dl=data['denovoStudies']
        try:
            dst = [vDB.get_study(d) for d in dl]
        except:
            print "The denovo study: %s DOES NOT EXIST! ...exiting!" % ' '.join(dl) 
            raise
        dvs = vDB.get_denovo_variants(dst)
    
    #response=Response(status.HTTP_200_OK,content_type='application/bin',mimetype='text/csv')
    response = HttpResponse(mimetype='text/csv')
    response['Content-Disposition'] = 'attachment; filename=unruly.csv'
    response['Expires'] = '0'
    response['Access-Control-Allow-Origin'] = '*'

    
    _safeVs(response,itertools.imap(augmentAVar,itertools.chain(dvs,[])),
                    ['effectType', 'effectDetails', 'all.altFreq','all.nAltAlls','all.nParCalled', '_par_races_', '_ch_prof_'],sep=",")
    return response



