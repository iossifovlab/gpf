# Create your views here.
from django.contrib.auth import get_user_model
# from django.contrib.auth.models import AnonymousUser
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.http import StreamingHttpResponse
# from rest_framework.response import Response as RestResponse
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.decorators import api_view, parser_classes, \
    authentication_classes, permission_classes
from rest_framework.parsers import JSONParser, FormParser
# from rest_framework import serializers
from rest_framework import status
# from api.report_pheno import get_supported_studies, get_supported_measures, \
#     pheno_calc, pheno_query

from DAE import vDB
from DAE import giDB
from VariantAnnotation import get_effect_types

import itertools
import string
# import uuid


from query_variants import \
    get_child_types, get_variant_types, \
    join_line

from dae_query import prepare_summary

from report_variants import build_stats

from studies import get_transmitted_studies_names, get_denovo_studies_names, \
    get_studies_summaries

from models import VerificationPath
from serializers import UserSerializer
from helpers.logger import LOGGER, log_filter
from query_prepare import EFFECT_GROUPS, build_effect_type_filter,\
    prepare_string_value
from api.query.wdae_query_variants import wdae_query_wrapper, \
    gene_set_loader2,\
    prepare_query_dict


@receiver(post_save, sender=get_user_model())
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)

# from query_prepare_bak import prepare_transmitted_studies


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
    query_params = request.query_params
    if 'effectFilter' not in query_params:
        effect_filter = 'all'
    else:
        effect_filter = string.lower(query_params['effectFilter'])
    LOGGER.info("effect_filter: %s", effect_filter)
    result = []
    if effect_filter == 'all':
        result = EFFECT_GROUPS['coding'] + EFFECT_GROUPS['noncoding']
    elif effect_filter == 'none':
        result = []
    elif effect_filter == 'lgds':
        result = EFFECT_GROUPS['lgds']
    elif effect_filter == 'coding':
        result = EFFECT_GROUPS['coding']
    elif effect_filter == 'nonsynonymous':
        result = EFFECT_GROUPS['nonsynonymous']
    elif effect_filter == 'utrs':
        result = EFFECT_GROUPS['utrs']
    elif effect_filter == 'noncoding':
        result = EFFECT_GROUPS['noncoding']
    elif effect_filter == 'cnv':
        result = EFFECT_GROUPS['cnv']
    else:
        result = "error: unsupported filter set name"
        return Response({'effect_filter': result},
                        status=status.HTTP_400_BAD_REQUEST)
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

    query_params = request.query_params
    if 'variantFilter' not in query_params:
        return Response({'variant_filters': all_var_types})

    variant_filter = string.upper(query_params['variantFilter'])
    LOGGER.info("variant_filter: %s", variant_filter)

    all_var_types = ['sub', 'ins', 'del', 'CNV']
    result = all_var_types
    if variant_filter == 'WHOLE EXOME':
        result = ['sub', 'ins', 'del']
    elif variant_filter == 'SSC':
        result = all_var_types
    elif not variant_filter or variant_filter == "ALL":
        result = all_var_types
    else:
        return Response({'variant_filters': "error: unsuported tab name (%s)" %
                         variant_filter},
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
    query_params = request.query_params
    all_result = ['autism',
                  'congenital heart disease',
                  'epilepsy',
                  'intelectual disability',
                  'schizophrenia',
                  'unaffected']

    if 'phenotypeFilter' not in query_params:
        return Response({'pheno_type_filters': all_result})

    phenotype_filter = string.upper(query_params['phenotypeFilter'])
    LOGGER.info("pheno_type_filters: %s", phenotype_filter)

    if phenotype_filter == 'WHOLE EXOME':
        result = all_result
    elif phenotype_filter == 'SSC':
        result = ['autism', 'unaffected', 'no child']
    elif not phenotype_filter or phenotype_filter == "ALL":
        result = all_result
    else:
        return Response({'pheno_type_filters':
                         "error: unsuported pheno group name (%s)" %
                         phenotype_filter},
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

    query_params = request.query_params
    if 'filter' in query_params:
        start_string = query_params['filter']
        families = [f for f in families if f.startswith(start_string)]

    return Response({'study': study_name,
                     'families': families})


def __get_page_count(query_params, page_count=30):
    if 'page_count' in query_params:
        page_count = prepare_string_value(query_params, 'page_count')
        try:
            page_count = int(page_count)
        except:
            page_count = 30
    if not (page_count > 0 and page_count <= 200):
        page_count = 30
    return page_count


def __gene_set_filter_response_dict(query_params, gts):
    page_count = __get_page_count(query_params, page_count=100)

    filter_string = None
    if 'filter' in query_params:
        filter_string = prepare_string_value(query_params, 'filter')

    if filter_string is not None:
        filter_string = filter_string.lower().strip()

        filter_by_key = prepare_string_value(query_params, 'key')
        filter_by_desc = prepare_string_value(query_params, 'desc')

        if filter_by_key == 'true':
            filter_by_key = True
        else:
            filter_by_key = False
        if filter_by_desc == 'true':
            filter_by_desc = True
        else:
            filter_by_desc = False

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
def gene_set_list2(request):
    """
    Returns list of gene set.

    Expected parameters are:

    * `gene_set` - the name of the gene set group;
    * `gene_set_phenotype` - if the gene set is `denovo`, we have to
        pass the gene set phenotype.
    """
    query_params = prepare_query_dict(request.query_params)
    if 'gene_set' not in query_params:
        return Response({})
    gene_set = prepare_string_value(query_params, 'gene_set')
    gene_set_phenotype = prepare_string_value(
        query_params, 'gene_set_phenotype') \
        if 'gene_set_phenotype' in query_params else None

    gene_name = prepare_string_value(query_params, 'gene_name') \
        if 'gene_name' in query_params else None

    gts = gene_set_loader2(gene_set, gene_set_phenotype)

    if gts:
        return __gene_set_response(query_params, gts, gene_name)
    else:
        return Response()


@api_view(['GET'])
def gene_set_download(request):
    """
    Returns list of gene symbols for given gene set.

    Expected parameters are:

    * `gene_set` - the name of the gene set group;
    * `gene_set_phenotype` - if the gene set is `denovo`, we have to
        pass the gene set phenotype;
    * `gene_name` - the gene set name.

    Returns:
    Single column comma separated file to download.
    """
    gene_syms = []

    query_params = prepare_query_dict(request.query_params)
    if 'gene_set' in query_params and 'gene_name' in query_params:
        gene_set = prepare_string_value(query_params, 'gene_set')
        gene_set_phenotype = \
            prepare_string_value(query_params, 'gene_set_phenotype') \
            if 'gene_set_phenotype' in query_params else None

        gene_name = prepare_string_value(query_params, 'gene_name')
        gts = gene_set_loader2(gene_set, gene_set_phenotype)
        if gts and gene_name in gts.t2G:
            title = "{}:{}".format(gene_set, gene_name)
            if gene_set_phenotype:
                title += " ({})".format(gene_set_phenotype)
            gene_syms.append('"{}"'.format(title))
            gene_syms.append('"{}"'.format(gts.tDesc[gene_name]))
            gene_syms.extend(gts.t2G[gene_name].keys())
    res = map(lambda s: "{}\r\n".format(s), gene_syms)
    response = StreamingHttpResponse(
        res,
        content_type='text/csv')

    response['Content-Disposition'] = 'attachment; filename=geneset.csv'
    response['Expires'] = '0'

    return response


@api_view(['GET'])
def gene_set_phenotypes(request):
    return Response(['autism',
                     'congenital heart disease',
                     "epilepsy",
                     'intelectual disability',
                     'schizophrenia',
                     'unaffected'])


@api_view(['GET'])
def study_tab_phenotypes(request, study_tab):
    """
    Returns phenotypes to use in study tab legend table.

    Accepts `study_tab` name as a URL parameter.

    Examples:

        GET /api/study_tab_phenotypes/ssc
        GET /api/study_tab_phenotypes/whole_exome
        GET /api/study_tab_phenotypes/variants
    """
    if study_tab == 'ssc':
        return Response(['autism',
                         'unaffected'])

    if study_tab == 'whole_exome' or study_tab == 'variants':
        return Response(['autism',
                         'congenital heart disease',
                         "epilepsy",
                         'intelectual disability',
                         'schizophrenia',
                         'unaffected'])
    return Response()


@api_view(['POST'])
@authentication_classes((TokenAuthentication,))
@permission_classes((IsAuthenticated,))
def query_variants_preview_full(request):
    query_variants_preview(request)


@api_view(['POST'])
def query_variants_preview(request):
    """
Performs a query to DAE. The body of the request should be JSON
formatted object containing all the parameters for the query.

Example JSON object describing the query is following:

    {
         "denovoStudies":["DalyWE2012"],
         "transmittedStudies":["wig683"],
         "inChild":"sibF",
         "effectTypes":"frame-shift",
         "variantTypes":"del",
         "ultraRareOnly":"True"
    }

All fields are same as in query_variants_bak request

    """

    if request.method == 'OPTIONS':
        return Response()

    data = prepare_query_dict(request.data)
    build_effect_type_filter(data)

    # if isinstance(data, QueryDict):
    #     data = prepare_query_dict(data)
    # else:
    #     data = prepare_query_dict(data)

    LOGGER.info(log_filter(request, "preview query variants: " + str(data)))
    data['limit'] = 2000
    generator = wdae_query_wrapper(data, atts=["_pedigree_", "phenoInChS"])
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
Performs a query to DAE. The body of the request should be JSON formatted
object containing all the parameters for the query.

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

    data = dict(request.data)
    build_effect_type_filter(data)

    LOGGER.info(log_filter(request, "query variants request: " + str(data)))

    comment = ', '.join([': '.join([k, str(v)]) for (k, v) in data.items()])

    generator = wdae_query_wrapper(data)
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
    if 'studies' not in request.query_params:
        return Response({})

    studies_names = request.query_params['studies']
    studies = vDB.get_studies(studies_names)

    stats = build_stats(studies)
    stats['studies_names'] = studies_names

    return Response(stats)


# @api_view(['GET'])
# def pheno_supported_studies(request):
#     return Response({"pheno_supported_studies": get_supported_studies()})


# @api_view(['GET'])
# def pheno_supported_measures(request):
#     return Response({"pheno_supported_measures": get_supported_measures()})


# @api_view(['POST'])
# def pheno_report_preview(request):
#
#     if request.method == 'OPTIONS':
#         return Response()
#
#     data = prepare_query_dict(request.data)
#     LOGGER.info(log_filter(request, "preview pheno report: " + str(data)))
#     ps = pheno_query(data)
#     res = pheno_calc(ps)
#
#     return Response(res)


def join_row(p, sep=','):
    r = [str(c) for c in p]
    return sep.join(r) + '\n'


# @api_view(['POST'])
# @parser_classes([JSONParser, FormParser])
# def pheno_report_download(request):
#
#     if request.method == 'OPTIONS':
#         return Response()
#
#     data = prepare_query_dict(request.data)
#     LOGGER.info(log_filter(request, "preview pheno download: " + str(data)))
#     comment = ', '.join([': '.join([k, str(v)]) for (k, v) in data.items()])
#
#     ps = pheno_query(data)
#     response = StreamingHttpResponse(
#         itertools.chain(
#             itertools.imap(join_row, ps),
#             ['# %s\n' % comment]),
#         content_type='text/csv')
#     response['Content-Disposition'] = 'attachment; filename=unruly.csv'
#     response['Expires'] = '0'
#
#     return response


@api_view(['POST'])
def register(request):
    serialized = UserSerializer(data=request.data)
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
    verif_path = request.data['verif_path']
    try:
        VerificationPath.objects.get(path=verif_path)
        return Response({}, status=status.HTTP_200_OK)
    except VerificationPath.DoesNotExist:
        return Response({
            'errors': 'Verification path does not exist.'},
            status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def change_password(request):
    password = request.data['password']
    verif_path = request.data['verif_path']

    user = get_user_model().change_password(verif_path, password)

    return Response({'username': user.email, 'password': password},
                    status.HTTP_201_CREATED)


@api_view(['POST'])
def get_user_info(request):
    token = request.data['token']
    try:
        user = Token.objects.get(key=token).user
        if (user.is_staff):
            userType = 'admin'
        else:
            userType = 'registered'

        return Response({'userType': userType,
                         'email': user.email}, status.HTTP_200_OK)
    except Token.DoesNotExist:
        return Response({}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def reset_password(request):
    email = request.data['email']
    user_model = get_user_model()
    try:
        user = user_model.objects.get(email=email)
        user.reset_password()

        return Response({}, status.HTTP_200_OK)
    except user_model.DoesNotExist:
        return Response({'errors': 'User with this email not found'},
                        status=status.HTTP_400_BAD_REQUEST)
