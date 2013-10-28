# Create your views here.
from django.http import HttpResponse
from django.conf import settings
  

from rest_framework.response import Response as RestResponse
from rest_framework.decorators import api_view

from rest_framework import status

from DAE import vDB, giDB, get_gene_sets_symNS,_safeVs

from GetVariantsInterface import augmentAVar

import itertools

from dae_query import dae_query_variants

class Response(RestResponse):
    def __init__(self,data=None, status=200,
                 template_name=None, headers=None,
                 exception=False, content_type=None):
        if headers is None:
            headers={'Access-Control-Allow-Origin':'*'}
        else:
            headers['Access-Control-Allow-Origin']='*'
        RestResponse.__init__(self,data,status,template_name,headers,exception,content_type)
    
@api_view(['GET'])
def denovo_studies_list(request):
    stds=vDB.getDenovoStudies()
    stgs=vDB.getStudyGroups()
    stds.extend(stgs)
    return Response({"denovo_studies" : [st for st in stds if st!='studyDir']})

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
    families=st.families.keys()
    
    query_params=request.QUERY_PARAMS
    if query_params.has_key('filter'):
        start_string=query_params['filter']
        families=[f for f in families if f.startswith(start_string)]
        
    return Response({'study':study_name,
                     'families':families})

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
    return Response(res) 
    
        
@api_view(['GET'])
def gene_set_go_list(request):
    gts=settings.GENE_SETS_GO
    res=__gene_set_filter_response_dict(request, gts.tDesc)
    return Response(res)

@api_view(['GET'])
def gene_set_disease_list(request):
    gts=settings.GENE_SETS_DISEASE
    res=__gene_set_filter_response_dict(request, gts.tDesc)
    return Response(res)

@api_view(['GET'])
def gene_set_denovo_list(request,denovo_study):
    gts = get_gene_sets_symNS('denovo',str(denovo_study))
    return Response(gts.tDesc) 


@api_view(['GET'])
def gene_list(request,page_count=30):
    gl=settings.GENE_SYMS_LIST

    query_params=request.QUERY_PARAMS
    
    if query_params.has_key('filter'):
        start_string=query_params['filter']
        gl=[g for g in gl if g.startswith(start_string)]
        
    page_count = __get_page_count(query_params, page_count)
        
    return Response(gl[:page_count])

@api_view(['POST'])
def get_variants_csv(request):
    """
Performs a query to DAE. The body of the request should be JSON formatted object containing
all the parameters for the query. 

Example JSON object describing the query is following:

    {
         "denovoStudies":["DalyWE2012"],
         "transmittedStudies":["wig683"],
         "inChild":"sibF",
         "effectTypes":"frame-shift",
         "variantTypes":"del",
         "ultraRareOnly":"True"
    }

The expected fields are:

* "denovoStudies" -- expects list of denovo studies
* "transmittedStudies" --- expects list of transmitted studies

* "geneSyms" --- comma separated list of gene symbols or list of gene symbols
* "geneSet" --- contains dictionary with two elements: "gs_id" is the gene set name (one of 'main','GO' or 'disease') and 'gs_term'. Example: `{'geneSet':{'gs_id':'GO', 'gs_term':'GO:2001293'}}` or `{'geneSet':{'gs_id':'main', 'gs_term':'mPFC_maternal'}}`

* "effectTypes" --- effect types
* "variantTypes" --- variant types
* "inChild" --- in child
* "familyIds" --- comma separated list of family Ids

* "ultraRareOnly" --- True of False
* "minAltFreqPrcnt" --- minimal frequency
* "maxAltFreqPrcnt" --- maximum frequency
 
    """
    
    if request.method == 'OPTIONS':
        print "get_variants_csv: OPTIONS"
        
        
        return Response()

    
    data=request.DATA
    vsl=dae_query_variants(data)
    
    response = HttpResponse(mimetype='text/csv')
    response['Content-Disposition'] = 'attachment; filename=unruly.csv'
    response['Expires'] = '0'
    response['Access-Control-Allow-Origin'] = '*'
    
    _safeVs(response,itertools.imap(augmentAVar,itertools.chain(*vsl)),
                    ['effectType', 'effectDetails', 'all.altFreq','all.nAltAlls','all.nParCalled', '_par_races_', '_ch_prof_'],sep=",")
    return response







