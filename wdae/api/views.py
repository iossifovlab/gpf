# Create your views here.
from django.conf import settings


# from rest_framework.response import Response as RestResponse
from rest_framework.response import Response
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import JSONParser, FormParser


from DAE import vDB, get_gene_sets_symNS

from GetVariantsInterface import augmentAVar

import itertools

from dae_query import dae_query_variants, generate_response

# class Response(RestResponse):
#     def __init__(self,data=None, status=200,
#                  template_name=None, headers=None,
#                  exception=False, content_type=None):
#         if headers is None:
#             headers={'Access-Control-Allow-Origin':'*'}
#         else:
#             headers['Access-Control-Allow-Origin']='*'
#         RestResponse.__init__(self,data,status,template_name,headers,exception,content_type)

@api_view(['GET'])
def denovo_studies_list(request):
    stds = [st for st in vDB.getDenovoStudies() if st != 'studyDir']
    stgs = [st for st in vDB.getStudyGroups() if st != 'studyDir']
    stds.extend(stgs)
    stds_desc = ['Description: %s \nDescription Description' % st for st in stds]
    return Response({"denovo_studies" : zip(stds, stds_desc)})

@api_view(['GET'])
def study_groups_list(request):
    stds = vDB.getStudyGroups()
    return Response({"study_groups" : stds})


@api_view(['GET'])
def transmitted_studies_list(request):
    stds = vDB.getTransmittedStudies()
    stds_desc = ['Description: %s \nDescription Description' % st for st in stds]
    return Response({"transmitted_studies" : zip(stds, stds_desc)})


@api_view(['GET'])
def effect_types_list(request):
    eff = vDB.get_effect_types()
    return Response({"effect_types" : eff})

@api_view(['GET'])
def variant_types_list(request):
    var_types = vDB.get_variant_types()
    return Response({'variant_types': var_types})

@api_view(['GET'])
def child_type_list(request):
    child_types = vDB.get_child_types()
    return Response({'child_types':child_types})

@api_view(['GET'])
def families_list(request, study_name = None):

    st = vDB.get_study(study_name)
    families = st.families.keys()

    query_params = request.QUERY_PARAMS
    if query_params.has_key('filter'):
        start_string = query_params['filter']
        families = [f for f in families if f.startswith(start_string)]

    return Response({'study':study_name,
                     'families':families})

def __get_page_count(query_params, page_count = 30):
    if query_params.has_key('page_count'):
        try:
            page_count = int(query_params['page_count'])
        except:
            page_count = 30
    if not (page_count > 0 and page_count <= 100):
        page_count = 30
    return page_count

def __gene_set_filter_response_dict(request, data):
    query_params = request.QUERY_PARAMS

    page_count = __get_page_count(query_params, page_count = 100)
    print "page_count:", page_count

    if query_params.has_key('filter'):
        filter_string = query_params['filter'].lower().strip()
        l = [(key, value) for (key, value) in data.items() if (filter_string in key.lower()) or (filter_string in value.lower())]
        return dict(l[0:page_count])
    else:
        return dict(data.items()[0:page_count])

def __gene_set_response(request, gts, gt):
    if gt is None:
        res = __gene_set_filter_response_dict(request, gts.tDesc)
        return Response(res)

    if str(gt) not in gts.tDesc.keys():
        return Response({})
    gl = gts.t2G[gt].keys()
    if not gl:
        return Response({})
    return Response({"gene_count":len(gl)})


@api_view(['GET'])
def gene_set_main_list(request, gene_set = None):
    return __gene_set_response(request, settings.GENE_SETS_MAIN, gene_set)


@api_view(['GET'])
def gene_set_go_list(request, gene_set = None):
    return __gene_set_response(request, settings.GENE_SETS_GO, gene_set)

@api_view(['GET'])
def gene_set_disease_list(request, gene_set = None):
    return __gene_set_response(request, settings.GENE_SETS_DISEASE, gene_set)

@api_view(['GET'])
def gene_set_denovo_list(request, denovo_study, gene_set = None):
    gts = get_gene_sets_symNS('denovo', str(denovo_study))
    return __gene_set_response(request, gts, gene_set)

@api_view(['GET'])
def gene_list(request, page_count = 30):
    gl = settings.GENE_SYMS_LIST

    query_params = request.QUERY_PARAMS

    if query_params.has_key('filter'):
        start_string = query_params['filter']
        gl = [g for g in gl if g.startswith(start_string)]

    page_count = __get_page_count(query_params, page_count)

    return Response(gl[:page_count])


from django.http import StreamingHttpResponse, QueryDict

def prepare_query_dict(data):
    res = []
    for (key, value) in data.items():
        key = str(key)
        if isinstance(value, list):
            value = [str(s) for s in value]
        else:
            value = str(value)
        res.append((key, value))
    return dict(res)

@api_view(['POST'])
@parser_classes([JSONParser, FormParser])
def query_variants(request):
    """
Performs a query to DAE. The body of the request should be JSON formatted object
containing all the parameters for the query.

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


* "geneSet" --- contains gene set name (one of 'main','GO' or 'disease')
* "geneTerm" --- contains gene set term. Example:  'GO:2001293' (from GO),
'mPFC_maternal' (from main).

* "geneRegion" --- gene region to filter (just a text field).

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


    data = request.DATA
    if isinstance(data, QueryDict):
        data = prepare_query_dict(data)

    vsl = dae_query_variants(data)
    print "query_variants: result ready; sending..."

    generator = generate_response(itertools.imap(augmentAVar, itertools.chain(*vsl)),
                                ['effectType',
                                 'effectDetails',
                                 'all.altFreq',
                                 'all.nAltAlls',
                                 'all.nParCalled',
                                 '_par_races_',
                                 '_ch_prof_'],
                                sep = ',')

    response = StreamingHttpResponse(generator, mimetype = 'text/csv')
    response['Content-Disposition'] = 'attachment; filename=unruly.csv'
    response['Expires'] = '0'

    #     response['Access-Control-Allow-Origin'] = '*'

    #     _safeVs(response,itertools.imap(augmentAVar,itertools.chain(*vsl)),
    #                     ['effectType', 'effectDetails', 'all.altFreq','all.nAltAlls','all.nParCalled', '_par_races_', '_ch_prof_'],sep=",")
    return response







