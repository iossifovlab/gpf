# Create your views here.
from django.http import StreamingHttpResponse

# from rest_framework.response import Response as RestResponse
from rest_framework.response import Response
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import JSONParser, FormParser


from DAE import vDB
from DAE import giDB 
from VariantAnnotation import get_effect_types

import itertools
import logging

from query_variants import do_query_variants, \
    get_child_types, get_variant_types, \
    join_line

from dae_query import prepare_summary, load_gene_set

from report_variants import build_stats
from enrichment import enrichment_results

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
def report_studies(request):
    return Response({"report_studies" : get_denovo_studies_names() + get_transmitted_studies_names()})

@api_view(['GET'])
def gene_sets_list(request):
    r = [{'label' : 'Main', 'val' : 'main', 'conf' : ['[[[', 'key', ']]]', '(((' , 'count', '))):', "desc"]},
    {'label' : 'GO', 'val' : 'GO' ,'conf' : ['key', 'count']},
    {'label' : 'Disease', 'val' : 'disease' ,'conf' : ['key', 'count']},
    {'label' : 'Denovo', 'val' : 'denovo' ,'conf' : ['---', 'key', '---', 'desc', '---', 'count']}]

    r = []
    for tsId in giDB.getGeneTermIds():
        label = giDB.getGeneTermAtt(tsId, "webLabel")
        formatStr = giDB.getGeneTermAtt(tsId, "webFormatStr")
        if not label or not formatStr:
            continue
        r.append({'label':label, 'val':tsId, 'conf':formatStr.split("|")})
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


def __gene_set_filter_response_dict(request, gts):
    query_params = request.QUERY_PARAMS

    page_count = __get_page_count(query_params, page_count = 100)
    print "page_count:", page_count

    if 'filter' in query_params:
        filter_string = query_params['filter'].lower().strip()

        filter_by_key = 0;
        filter_by_desc = 0;

        if query_params['key'] == 'true':
            filter_by_key = 1;
        if query_params['desc'] == 'true':
            filter_by_desc = 1;

        l = [(key, {"desc" : value, "count" : len(gts.t2G[key].keys())}) for (key, value) in gts.tDesc.items() if key in gts.t2G and (filter_string in key.lower() and filter_by_key) or (filter_string in value.lower() and filter_by_desc)]
        return dict(l[0:page_count])
    else:
        l = [(key, {"desc" : value, "count" : len(gts.t2G[key].keys())}) for (key, value) in gts.tDesc.items() if key in gts.t2G]
        return dict(l[0:page_count])


def __gene_set_response(request, gts, gt):
    if gt is None:
        res = __gene_set_filter_response_dict(request, gts)
        return Response(res)

    if str(gt) not in gts.tDesc.keys():
        return Response({})
    gl = gts.t2G[gt].keys()
    if not gl:
        return Response({})
    return Response({"gene_count": len(gl)})

@api_view(['GET'])
def gene_set_list(request):
    query_params = request.QUERY_PARAMS
    if 'gene_set' not in query_params:
        return Response({})
    gene_set = query_params['gene_set']
    gene_name = query_params['gene_name'] if 'gene_name' in query_params else None
    study_name = str(query_params['study']) if 'study' in query_params else None

    gts = load_gene_set(gene_set, study_name)

    if gts:
        return __gene_set_response(request, gts, gene_name)
    else:
        return Response()

# @api_view(['GET'])
# def gene_set_main_list(request, gene_set=None):
#     return __gene_set_response(request, settings.GENE_SETS_MAIN, gene_set)


# @api_view(['GET'])
# def gene_set_go_list(request, gene_set=None):
#     return __gene_set_response(request, settings.GENE_SETS_GO, gene_set)

# @api_view(['GET'])
# def gene_set_disease_list(request, gene_set=None):
#     return __gene_set_response(request, settings.GENE_SETS_DISEASE, gene_set)

# @api_view(['GET'])
# def gene_set_denovo_list(request, denovo_study, gene_set = None):
#     gts = get_gene_sets_symNS('denovo', str(denovo_study))
#     return __gene_set_response(request, gts, gene_set)

# @api_view(['GET'])
# def gene_list(request, page_count=30):
#     query_params = request.QUERY_PARAMS

#     if 'filter' not in query_params:
#         start_string = query_params['filter']
#         gl = [g for g in gl if g.startswith(start_string)]

#     page_count = __get_page_count(query_params, page_count)

#     return Response(gl[:page_count])


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
        return Response()

    data = prepare_query_dict(request.DATA)
    # if isinstance(data, QueryDict):
    #     data = prepare_query_dict(data)
    # else:
    #     data = prepare_query_dict(data)

    logger.info("preview query variants: " + str(data))

    generator = do_query_variants(data, gene_set_loader=load_gene_set)
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

    data = prepare_query_dict(request.DATA)
    # if isinstance(data, QueryDict):
    #     data = prepare_query_dict(data)
    logger.info("query variants request: " + str(data))

    generator = do_query_variants(data, gene_set_loader=load_gene_set)
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


@api_view(['GET'])
def enrichment_test(request):
    """
Performs enrichment test. Expected parameters are:

    * dst_name - denovo study name;
    * tst_name - transmitted study name;
    * gt_name - gene term name;
    * gs_name - gene set name;

Examples:

    GET /api/enrichment_test?dst_name=allWE&tst_name=w873e374s322&gt_name=main&gs_name=ChromatinModifiers
    """
    if 'dst_name' not in request.QUERY_PARAMS:
        return Response()
    if 'tst_name' not in request.QUERY_PARAMS:
        return Response()
    if 'gt_name' not in request.QUERY_PARAMS:
        return Response()
    if 'gs_name' not in request.QUERY_PARAMS:
        return Response()
    dst_name = request.QUERY_PARAMS['dst_name']
    tst_name = request.QUERY_PARAMS['tst_name']
    gt_name = request.QUERY_PARAMS['gt_name']
    gs_name = request.QUERY_PARAMS['gs_name']

    res = enrichment_results(dst_name, tst_name, gt_name, gs_name)
    return Response(res)
