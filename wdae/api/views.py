# Create your views here.
from django.conf import settings
from django.http import StreamingHttpResponse, QueryDict

# from rest_framework.response import Response as RestResponse
from rest_framework.response import Response
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import JSONParser, FormParser


from DAE import vDB, get_gene_sets_symNS
from VariantAnnotation import get_effect_types

import itertools
import logging

from dae_query import do_query_variants, \
    get_child_types, get_variant_types, \
    join_line, prepare_summary

from report_variants import build_stats

from studies import get_transmitted_studies_names, get_denovo_studies_names


# class Response(RestResponse):
#     def __init__(self,data=None, status=200,
#                  template_name=None, headers=None,
#                  exception=False, content_type=None):
#         if headers is None:
#             headers={'Access-Control-Allow-Origin':'*'}
#         else:
#             headers['Access-Control-Allow-Origin']='*'
#         RestResponse.__init__(self,data,status,template_name,headers,exception,content_type)


logger = logging.getLogger(__name__)

@api_view(['GET'])
def gene_sets_list(request):
    r = ['Main', 'GO', 'Disease', 'Denovo']
    return Response({"gene_sets" : r})

@api_view(['GET'])
def denovo_studies_list(request):
    r = get_denovo_studies_names()
    return Response({"denovo_studies": r})


@api_view(['GET'])
def study_groups_list(request):
    stds = vDB.getStudyGroups()
    return Response({"study_groups": stds})

@api_view(['GET'])
def transmitted_studies_list(request):
    r = get_transmitted_studies_names()
    return Response({"transmitted_studies": r})


@api_view(['GET'])
def effect_types_list(request):
    eff = ['All'] + get_effect_types(types=False, groups=True) + \
        get_effect_types(types=True, groups=False)
    return Response({"effect_types": eff})

@api_view(['GET'])
def variant_types_list(request):
    # var_types = vDB.get_variant_types()
    # re-think
    # var_types = ['All', 'CNV+', 'CNV-', 'snv', 'ins', 'del']
    # moved to dae_query; I need them in several places
    var_types = get_variant_types()
    return Response({'variant_types': var_types})

@api_view(['GET'])
def child_type_list(request):
    # child_types = vDB.get_child_types()
    # re-think at some point in the future
    # child_types = ['prb', 'sib', 'prbM', 'sibF', 'sibM', 'prbF']
    # moved to dae_query; I need them in several places
    child_types = get_child_types()
    return Response({'child_types': child_types})

@api_view(['GET'])
def families_list(request, study_name=None):

    st = vDB.get_study(study_name)
    families = st.families.keys()

    query_params = request.QUERY_PARAMS
    if 'filter' in query_params:
        start_string = query_params['filter']
        families = [f for f in families if f.startswith(start_string)]

    return Response({'study': study_name,
                     'families': families})


def __get_page_count(query_params, page_count=30):
    if 'page_count' in query_params:
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

    if 'filter' in query_params:
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
    return Response({"gene_count": len(gl)})

@api_view(['GET'])
def gene_set_list(request, page_count, gene_set):
    print "PRINTTTTTTT " + gene_set
    return Reponse({'ala' : 'bala'})

@api_view(['GET'])
def gene_set_main_list(request, gene_set=None):
    return __gene_set_response(request, settings.GENE_SETS_MAIN, gene_set)


@api_view(['GET'])
def gene_set_go_list(request, gene_set=None):
    return __gene_set_response(request, settings.GENE_SETS_GO, gene_set)

@api_view(['GET'])
def gene_set_disease_list(request, gene_set=None):
    return __gene_set_response(request, settings.GENE_SETS_DISEASE, gene_set)

@api_view(['GET'])
def gene_set_denovo_list(request, denovo_study, gene_set = None):
    gts = get_gene_sets_symNS('denovo', str(denovo_study))
    return __gene_set_response(request, gts, gene_set)

@api_view(['GET'])
def gene_list(request, page_count=30):
    gl = settings.GENE_SYMS_LIST

    query_params = request.QUERY_PARAMS

    if 'filter' not in query_params:
        start_string = query_params['filter']
        gl = [g for g in gl if g.startswith(start_string)]

    page_count = __get_page_count(query_params, page_count)

    return Response(gl[:page_count])


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
def query_variants_preview(request):
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

All fields are same as in query_variants request

    """

    if request.method == 'OPTIONS':
        print "get_variants_csv: OPTIONS"

        return Response()

    data = request.DATA
    if isinstance(data, QueryDict):
        data = prepare_query_dict(data)

    generator = do_query_variants(data)
    summary = prepare_summary(generator)

    return Response(summary)



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

Advanced family filter expects following fields:

* 'familyRace' --- family race
* 'familyPrbGender' --- proband gender; possible values: 'male', 'female'
* 'familySibGender' --- sibling gender; possible values: 'male', 'female'
* 'familyVerbalIqHi' --- verbal IQ high limit (default is inf)
* 'familyVerbalIqLo' --- verbal IQ low limit (default is 0)
* 'familyQuadTrio' --- Trio/Quad family; possible values are: 'trio' and 'quad'


    """

    if request.method == 'OPTIONS':
        print "get_variants_csv: OPTIONS"

        return Response()

    data = request.DATA
    if isinstance(data, QueryDict):
        data = prepare_query_dict(data)
    logger.info("query variants request: " + str(data))

    generator = do_query_variants(data)
    response = StreamingHttpResponse(
        itertools.imap(join_line, generator), content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename=unruly.csv'
    response['Expires'] = '0'

    return response


@api_view(['GET'])
def report_variants(request):
    """
Performs query to DAE to generate report similar to 'reportVariantNumbers.py'.

Expects list of studies names as comma separated list in the query parameters
with name 'studies'.

Examples:

     GET /api/report_variants?studies=IossifovWE2012,DalyWE2012
     GET /api/report_variants?studies=IossifovWE2012
     GET /api/report_variants?studies=DalyWE2012

    """
    if 'studies' not in request.QUERY_PARAMS:
        return Response({})

    studies_names = request.QUERY_PARAMS['studies']
    studies = vDB.get_studies(studies_names)

    stats = build_stats(studies)
    stats['studies_names'] = studies_names

    return Response(stats)
