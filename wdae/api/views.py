# Create your views here.
from django.contrib.auth import get_user_model
# from django.contrib.auth.models import AnonymousUser
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.http import StreamingHttpResponse
from django.http import QueryDict
# from rest_framework.response import Response as RestResponse
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.decorators import api_view, parser_classes, authentication_classes, permission_classes
from rest_framework.parsers import JSONParser, FormParser
# from rest_framework import serializers
from rest_framework import status

from DAE import vDB
from DAE import giDB
from VariantAnnotation import get_effect_types

import itertools
import logging
import string
import operator
# import uuid

from query_variants import do_query_variants, \
    get_child_types, get_variant_types, \
    join_line

from query_prepare import prepare_ssc_filter

from dae_query import prepare_summary, load_gene_set, load_gene_set2

from report_variants import build_stats
from enrichment_query import \
    enrichment_results_by_phenotype, \
    enrichment_prepare

from studies import get_transmitted_studies_names, get_denovo_studies_names, \
    get_studies_summaries

from models import VerificationPath
from serializers import UserSerializer

@receiver(post_save, sender=get_user_model())
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)

# from query_prepare import prepare_transmitted_studies


# class Response(RestResponse):
#     def __init__(self,data=None, status=200,
#                  template_name=None, headers=None,
#                  exception=False, content_type=None):
#         if headers is None:
#             headers={'Access-Control-Allow-Origin':'*'}
#         else:
#             headers['Access-Control-Allow-Origin']='*'
#         RestResponse.__init__(self,data,status,template_name,headers,exception,content_type)

logger = logging.getLogger('wdae.api')

def log_filter(request, message):
    request_method = getattr(request, 'method', '-')
    path_info = getattr(request, 'path_info', '-')
    # Headers
    META = getattr(request, 'META', {})
    remote_addr = META.get('REMOTE_ADDR', '-')
    # server_protocol = META.get('SERVER_PROTOCOL', '-')
    # http_user_agent = META.get('HTTP_USER_AGENT', '-')
    return "remote addr: %s; method: %s; path: %s; %s" % (remote_addr,
                                                          request_method,
                                                          path_info,
                                                          message)

@api_view(['GET'])
def report_studies(request):
    return Response({"report_studies": get_denovo_studies_names() +
                     get_transmitted_studies_names()})


@api_view(['GET'])
def studies_summaries(request):
    return Response(get_studies_summaries())



@api_view(['GET'])
def gene_sets_list(request):
    r = []
    for tsId in giDB.getGeneTermIds():
        label = giDB.getGeneTermAtt(tsId, "webLabel")
        formatStr = giDB.getGeneTermAtt(tsId, "webFormatStr")
        if not label or not formatStr:
            continue
        r.append({'label': label, 'val': tsId, 'conf': formatStr.split("|")})

    return Response({"gene_sets": r})


@api_view(['GET'])
def denovo_studies_list(request):
    r = get_denovo_studies_names()
    return Response({"denovo_studies": r})


@api_view(['GET'])
def transmitted_studies_list(request):
    r = get_transmitted_studies_names()

    return Response({"transmitted_studies": r})


__EFFECT_TYPES = {
    "Nonsense": ["nonsense"],
    "Frame-shift": ["frame-shift"],
    "Splice-site": ["splice-site"],
    "Missense": ["missense"],
    "Non-frame-shift": ["no-frame-shift"],
    "noStart": ["noStart"],
    "noEnd": ["noEnd"],
    "Synonymous": ["synonymous"],
    "Non coding": ["non-coding"],
    "Intron": ["intron"],
    "Intergenic": ["intergenic"],
    "3'-UTR": ["3'UTR", "3'UTR-intron"],
    "5'-UTR": ["5'UTR", "5'UTR-intron"],
    "CNV": ["CNV+", "CNV-"],

}


__EFFECT_GROUPS = {
    "coding":[
        "Nonsense",
        "Frame-shift",
        "Splice-site",
        "Missense",
        "Non-frame-shift",
        "noStart",
        "noEnd",
        "Synonymous",
    ],
    "noncoding": [
        "Non coding",
        "Intron",
        "Intergenic",
        "3'-UTR",
        "5'-UTR",
    ],
    "cnv": [
        "CNV+",
        "CNV-"
    ],
    "lgds": [
        "Nonsense",
        "Frame-shift",
        "Splice-site",
    ],
    "nonsynonymous": [
        "Nonsense",
        "Frame-shift",
        "Splice-site",
        "Missense",
        "Non-frame-shift",
        "noStart",
        "noEnd",
    ],
    "utrs": [
        "3'-UTR",
        "5'-UTR",
    ]

}


def build_effect_type_filter(data):
    if "effectTypes" not in data:
        return
    effects_string = data['effectTypes']
    effects = effects_string.split(',')
    result_effects = reduce(operator.add,
                            [__EFFECT_TYPES[et]  if et in __EFFECT_TYPES else [et] for et in effects])
    data["effectTypes"] = ','.join(result_effects)


@api_view(['GET'])
def effect_types_filters(request):
    """
Effect types filters list.

Request expects 'effectFilter' with posible values:

    * ALL
    * NONE
    * LGDs
    * coding
    * nonsynonymous
    * UTRs
    * noncoding
    * CNV

Example:

    GET /api/effect_types_filters?effectFilter=UTRs

    """
    query_params = request.QUERY_PARAMS
    if 'effectFilter' not in query_params:
        effect_filter = 'all'
    else:
        effect_filter = string.lower(query_params['effectFilter'])
    logger.info("effect_filter: %s", effect_filter)
    result = []
    if effect_filter == 'all':
        result = __EFFECT_GROUPS['coding'] + __EFFECT_GROUPS['noncoding']
    elif effect_filter == 'none':
        result = []
    elif effect_filter == 'lgds':
        result = __EFFECT_GROUPS['lgds']
    elif effect_filter == 'coding':
        result = __EFFECT_GROUPS['coding']
    elif effect_filter == 'nonsynonymous':
        result = __EFFECT_GROUPS['nonsynonymous']
    elif effect_filter == 'utrs':
        result = __EFFECT_GROUPS['utrs']
    elif effect_filter == 'noncoding':
        result = __EFFECT_GROUPS['noncoding']
    elif effect_filter == 'cnv':
        result = __EFFECT_GROUPS['cnv']
    else:
        result = "error: unsupported filter set name"
        return Response({'effect_filter': result}, status=status.HTTP_400_BAD_REQUEST)
    return Response({'effect_filter': result})


@api_view(['GET'])
def effect_types_list(request):
    eff = ['All'] + get_effect_types(types=False, groups=True) + \
        get_effect_types(types=True, groups=False)
    return Response({"effect_types": eff})


@api_view(['GET'])
def chromes_effect_types(request):
    from VariantAnnotation import LOF, nonsyn
    return Response({"LoF": LOF,
                     "nonsyn": nonsyn})

@api_view(['GET'])
def variant_types_filters(request):
    """
Variant types filters list.

Request expects 'variantFilter' with posible values:

    * ALL
    * SSC
    * WHOLE EXOME

Example:

    GET /api/variant_types_filters?variantFilter=SSC

    """
    all_var_types = ['sub', 'ins', 'del', 'CNV']

    query_params = request.QUERY_PARAMS
    if 'variantFilter' not in query_params:
        return Response({'variant_filters': all_var_types})

    variant_filter = string.upper(query_params['variantFilter'])
    logger.info("variant_filter: %s", variant_filter)

    all_var_types = ['sub', 'ins', 'del', 'CNV']
    result = all_var_types
    if variant_filter == 'WHOLE EXOME':
        result = ['sub', 'ins', 'del']
    elif variant_filter == 'SSC':
        result = all_var_types
    elif not variant_filter or variant_filter == "ALL":
        result = all_var_types
    else:
        return Response({'variant_filters': "error: unsuported tab name (%s)" % variant_filter},
                        status=status.HTTP_400_BAD_REQUEST)

    return Response({'variant_filters': result})

@api_view(['GET'])
def variant_types_list(request):
    # var_types = vDB.get_variant_types()
    # re-think
    # var_types = ['All', 'CNV+', 'CNV-', 'snv', 'ins', 'del']
    # moved to dae_query; I need them in several places
    var_types = get_variant_types()
    return Response({'variant_types': var_types})

@api_view(['GET'])
def pheno_types_filters(request):
    query_params = request.QUERY_PARAMS
    all_result = ['autism', 'congenital heart disease', 'epilepsy', 'intelectual disability',
                  'schizophrenia','unaffected']

    if 'phenotypeFilter' not in query_params:
        return Response({'pheno_type_filters': all_result})

    phenotype_filter = string.upper(query_params['phenotypeFilter'])
    logger.info("pheno_type_filters: %s", phenotype_filter)

    if phenotype_filter == 'WHOLE EXOME':
        result = all_result
    elif phenotype_filter == 'SSC':
        result = ['autism', 'unaffected', 'no child']
    elif not phenotype_filter or phenotype_filter == "ALL":
        result = all_result
    else:
        return Response({'pheno_type_filters': "error: unsuported pheno group name (%s)" % phenotype_filter},
                        status=status.HTTP_400_BAD_REQUEST)

    return Response({'pheno_type_filters': result})



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
    if not (page_count > 0 and page_count <= 200):
        page_count = 30
    return page_count


def __gene_set_filter_response_dict(query_params, gts):
    page_count = __get_page_count(query_params, page_count=100)

    if 'filter' in query_params:
        filter_string = query_params['filter'].lower().strip()

        filter_by_key = 0
        filter_by_desc = 0

        if query_params['key'] == 'true':
            filter_by_key = 1
        if query_params['desc'] == 'true':
            filter_by_desc = 1

        l = [(key, {"desc": value, "count": len(gts.t2G[key].keys())})
             for (key, value) in gts.tDesc.items() if key in gts.t2G and
             (filter_string in key.lower() and filter_by_key) or
             (filter_string in value.lower() and filter_by_desc)]
        return dict(l[0:page_count])
    else:
        l = [(key, {"desc": value, "count": len(gts.t2G[key].keys())})
             for (key, value) in gts.tDesc.items() if key in gts.t2G]
        return dict(l[0:page_count])


def __gene_set_response(query_params, gts, gt):
    if gt is None:
        res = __gene_set_filter_response_dict(query_params, gts)
        return Response(res)

    if str(gt) not in gts.tDesc.keys():
        return Response({})
    gl = gts.t2G[gt].keys()
    if not gl:
        return Response({})
    return Response({"gene_count": len(gl), "key": gt, "desc": gts.tDesc[gt]})


@api_view(['GET'])
def gene_set_list(request):
    query_params = prepare_query_dict(request.QUERY_PARAMS)
    if 'gene_set' not in query_params:
        return Response({})
    gene_set = query_params['gene_set']
    gene_name = query_params['gene_name'] if 'gene_name' in query_params else None
    study_name = str(query_params['study']) if 'study' in query_params else None

    gts = load_gene_set(gene_set, study_name)

    if gts:
        return __gene_set_response(query_params, gts, gene_name)
    else:
        return Response()


@api_view(['GET'])
def gene_set_list2(request):
    query_params = prepare_query_dict(request.QUERY_PARAMS)
    if 'gene_set' not in query_params:
        return Response({})
    gene_set = query_params['gene_set']
    gene_name = query_params['gene_name'] if 'gene_name' in query_params else None
    gene_set_phenotype = str(query_params['gene_set_phenotype']) \
                        if 'gene_set_phenotype' in query_params else None

    gts = load_gene_set2(gene_set, gene_set_phenotype)

    if gts:
        return __gene_set_response(query_params, gts, gene_name)
    else:
        return Response()


def prepare_query_dict(data):
    res = []
    if isinstance(data, QueryDict):
        items = data.iterlists()
    else:
        items = data.items()

    for (key, val) in items:
        key = str(key)
        if isinstance(val, list):
            print "value:", val,
            value = ','.join([str(s).strip() for s in val])
            print "after: ", value
        else:
            value = str(val)

        res.append((key, value))

    return dict(res)


@api_view(['POST'])
@authentication_classes((TokenAuthentication,))
@permission_classes((IsAuthenticated,))
def query_variants_preview_full(request):
    query_variants_preview(request)

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
    build_effect_type_filter(data)

    # if isinstance(data, QueryDict):
    #     data = prepare_query_dict(data)
    # else:
    #     data = prepare_query_dict(data)

    logger.info(log_filter(request, "preview query variants: " + str(data)))

    generator = do_query_variants(data, atts=["_pedigree_", "phenoInChS"])
    summary = prepare_summary(generator)

    return Response(summary)


@api_view(['POST'])
@authentication_classes((TokenAuthentication,))
@permission_classes((IsAdminUser,))
@parser_classes([JSONParser, FormParser])
def query_variants_full(request):
    query_variants(request)


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
        return Response()

    data = prepare_query_dict(request.DATA)
    build_effect_type_filter(data)

    logger.info(log_filter(request, "query variants request: " + str(data)))

    comment = ', '.join([': '.join([k, str(v)]) for (k, v) in data.items()])

    generator = do_query_variants(data)
    response = StreamingHttpResponse(
        itertools.chain(
            itertools.imap(join_line, generator),
            ['# %s' % comment]),
        content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename=unruly.csv'
    response['Expires'] = '0'

    return response

@api_view(['POST'])
@authentication_classes((TokenAuthentication,))
@permission_classes((IsAuthenticated,))
def ssc_query_variants_preview(request):

    if request.method == 'OPTIONS':
        return Response()

    data = prepare_query_dict(request.DATA)
    data = prepare_ssc_filter(data)
    build_effect_type_filter(data)

    logger.info(log_filter(request, "preview query variants: " + str(data)))

    generator = do_query_variants(data, atts=["_pedigree_", "phenoInChS"])
    summary = prepare_summary(generator)
    return Response(summary)

@api_view(['POST'])
@parser_classes([JSONParser, FormParser])
def ssc_query_variants(request):
    if request.method == 'OPTIONS':
        return Response()

    data = prepare_query_dict(request.DATA)
    data = prepare_ssc_filter(data)
    build_effect_type_filter(data)

    logger.info(log_filter(request, "query variants request: " + str(data)))

    comment = ', '.join([': '.join([k, str(v)]) for (k, v) in data.items()])

    generator = do_query_variants(data)
    response = StreamingHttpResponse(
        itertools.chain(
            itertools.imap(join_line, generator),
            ['# %s' % comment]),
        content_type='text/csv')
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


# @api_view(['GET'])
# def enrichment_test(request):
#     """
# Performs enrichment test. Expected parameters are:
# 
# * "denovoStudies" -- expects list of denovo studies
# * "transmittedStudies" --- expects list of transmitted studies
# 
# * "geneSyms" --- comma separated list of gene symbols or list of gene symbols
# 
# 
# * "geneSet" --- contains gene set name (one of 'main','GO' or 'disease')
# * "geneTerm" --- contains gene set term. Example:  'GO:2001293' (from GO),
# 'mPFC_maternal' (from main).
# * "geneStudy --- if geneSet is 'denovo', then we expect this additional parameter, to
#     specify which denovo study to use
# 
# 
#     * dst_name - denovo study name;
#     * tst_name - transmitted study name;
#     * gt_name - gene term name;
#     * gs_name - gene set name;
# 
# Examples:
# 
#     GET /api/enrichment_test?denovoStudies=allWEAndTH&transmittedStudies=w873e374s322&geneTerm=ChromatinModifiers&geneSet=main"""
#     query_data = prepare_query_dict(request.QUERY_PARAMS)
#     logger.info(log_filter(request, "enrichment query: %s" % str(query_data)))
# 
#     data = enrichment_prepare(query_data)
#     # if isinstance(data, QueryDict):
#     #     data = prepare_query_dict(data)
# 
#     print "enrichment query:", data
# 
#     if data is None:
#         return Response(None)
# 
#     res = enrichment_results(**data)
#     return Response(res)


@api_view(['GET'])
def enrichment_test_by_phenotype(request):
    """
Performs enrichment test. Expected parameters are:

* "denovoStudies" -- expects list of denovo studies
* "transmittedStudies" --- expects list of transmitted studies

* "geneSyms" --- comma separated list of gene symbols or list of gene symbols


* "geneSet" --- contains gene set name (one of 'main','GO' or 'disease')
* "geneTerm" --- contains gene set term. Example:  'GO:2001293' (from GO),
'mPFC_maternal' (from main).
* "geneStudy --- if geneSet is 'denovo', then we expect this additional parameter, to
    specify which denovo study to use


    * dst_name - denovo study name;
    * tst_name - transmitted study name;
    * gt_name - gene term name;
    * gs_name - gene set name;

Examples:
    GET /api/enrichment_test_by_phenotype?denovoStudies=ALL+WHOLE+EXOME&transmittedStudies=w873e374s322&geneTerm=ChromatinModifiers&geneSet=main

    """

    query_data = prepare_query_dict(request.QUERY_PARAMS)
    logger.info(log_filter(request, "enrichment query by phenotype: %s" % str(query_data)))

    data = enrichment_prepare(query_data)
    # if isinstance(data, QueryDict):
    #     data = prepare_query_dict(data)

    if data is None:
        return Response(None)

    res = enrichment_results_by_phenotype(**data)
    return Response(res)

from api.report_pheno import get_supported_studies, get_supported_measures, \
    pheno_calc, pheno_query


@api_view(['GET'])
def pheno_supported_studies(request):
    return Response({"pheno_supported_studies": get_supported_studies()})

@api_view(['GET'])
def pheno_supported_measures(request):
    return Response({"pheno_supported_measures": get_supported_measures()})

@api_view(['POST'])
def pheno_report_preview(request):

    if request.method == 'OPTIONS':
        return Response()

    data = prepare_query_dict(request.DATA)
    logger.info(log_filter(request, "preview pheno report: " + str(data)))
    ps = pheno_query(data)
    res = pheno_calc(ps)

    return Response(res)

def join_row(p, sep=','):
    r = [str(c) for c in p]
    return sep.join(r) + '\n'

@api_view(['POST'])
@parser_classes([JSONParser, FormParser])
def pheno_report_download(request):

    if request.method == 'OPTIONS':
        return Response()

    data = prepare_query_dict(request.DATA)
    logger.info(log_filter(request, "preview pheno download: " + str(data)))
    comment = ', '.join([': '.join([k, str(v)]) for (k, v) in data.items()])

    ps = pheno_query(data)
    response = StreamingHttpResponse(
        itertools.chain(
            itertools.imap(join_row, ps),
            ['# %s\n' % comment]),
        content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename=unruly.csv'
    response['Expires'] = '0'

    return response

@api_view(['POST'])
def register(request):
    serialized = UserSerializer(data=request.DATA)
    if serialized.is_valid():
        user = get_user_model()
        researcher_id = serialized.validated_data['researcher_id']
        email = serialized.validated_data['email']

        created_user = user.objects.create_user(email, researcher_id)
        created_user.first_name = serialized.validated_data['first_name']
        created_user.last_name = serialized.validated_data['last_name']

        created_user.save()
        return Response(serialized.data, status=status.HTTP_201_CREATED)
    else:
        return Response(serialized._errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def check_verif_path(request):
    verif_path = request.DATA['verif_path']
    try:
        VerificationPath.objects.get(path=verif_path)
        return Response({}, status=status.HTTP_200_OK)
    except VerificationPath.DoesNotExist:
        return Response({
                        'errors': 'Verification path does not exist.'
                    }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def change_password(request):
    password = request.DATA['password']
    verif_path = request.DATA['verif_path']

    user = get_user_model().change_password(verif_path, password)

    return Response({'username': user.email, 'password': password }, status.HTTP_201_CREATED)

@api_view(['POST'])
def get_user_info(request):
    token = request.DATA['token']
    try:
        user = Token.objects.get(key=token).user
        print user
        if (user.is_staff):
            userType = 'admin'
        else:
            userType = 'registered'

        return Response({ 'userType': userType, 'email': user.email }, status.HTTP_200_OK)
    except Token.DoesNotExist:
        return Response({}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def reset_password(request):
    email = request.DATA['email']
    user_model = get_user_model()
    try:
        user = user_model.objects.get(email=email)
        user.reset_password()

        return Response({}, status.HTTP_200_OK)
    except user_model.DoesNotExist:
        return Response({
                        'errors': 'User with this email not found'
                    }, status=status.HTTP_400_BAD_REQUEST)
