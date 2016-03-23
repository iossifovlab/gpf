from django.conf.urls import patterns, url, include

from rest_framework.urlpatterns import format_suffix_patterns
from rest_framework.authtoken import views as rest_views
from api.enrichment.views import EnrichmentView
from api.sd.views import SequencingDenovoPreview, SequencingDenovoDownload
from api.ssc.views import SSCPreview, SSCDownload
from reports.views import VariantReportsView, FamiliesDataDownloadView

urlpatterns = patterns(
    'api.views',
    url(r'^denovo_studies$', 'denovo_studies_list'),
    # url(r'^study_groups$', 'study_groups_list'),
    url(r'^transmitted_studies$', 'transmitted_studies_list'),
    url(r'^effect_types$', 'effect_types_list'),
    url(r'^effect_types_filters$', 'effect_types_filters'),
    url(r'^chromes_effect_types$', 'chromes_effect_types'),
    url(r'^variant_types$', 'variant_types_list'),
    url(r'^variant_types_filters$', 'variant_types_filters'),

    url(r'^pheno_types_filters$', 'pheno_types_filters'),

    url(r'^families/(?P<study_name>.+)$', 'families_list'),

    url(r'^query_variants_preview$', 'query_variants_preview'),
    url(r'^query_variants$', 'query_variants'),

    url(r'^ssc_query_variants_preview$', SSCPreview.as_view()),
    url(r'^ssc_query_variants$', SSCDownload.as_view()),

    url(r'^we_query_variants_preview$', SequencingDenovoPreview.as_view()),
    url(r'^we_query_variants$', SequencingDenovoDownload.as_view()),

    url(r'^sd_query_variants_preview$', SequencingDenovoPreview.as_view()),
    url(r'^sd_query_variants$', SequencingDenovoDownload.as_view()),

    url(r'^report_variants$', 'report_variants'),

    url(r'^reports/variant_reports/(?P<study_name>.+)$',
        VariantReportsView.as_view()),
    url(r'^reports/families_data/(?P<study_name>.+)$',
        FamiliesDataDownloadView.as_view()),

    url(r'^gene_sets$', 'gene_sets_list'),
    # url(r'^gene_set_list$', 'gene_set_list'),
    url(r'^gene_set_list2$', 'gene_set_list2'),
    url(r'^gene_set_download$', 'gene_set_download'),

    url(r'^study_tab_phenotypes/(?P<study_tab>.+)$', 'study_tab_phenotypes'),
    url(r'^gene_set_phenotypes$', 'gene_set_phenotypes'),

    url(r'^report_studies$', 'report_studies'),
    url(r'^enrichment_test_by_phenotype$', EnrichmentView.as_view()),
    # url(r'^enrichment_test_by_phenotype$', 'enrichment_test_by_phenotype'),
    url(r'^child_types$', 'child_type_list'),
    url(r'^studies_summaries$', 'studies_summaries'),
    url(r'^users/register$', 'register'),
    url(r'^users/get_user_info$', 'get_user_info'),
    url(r'^users/check_verif_path', 'check_verif_path'),
    url(r'^users/change_password', 'change_password'),
    url(r'^users/reset_password', 'reset_password'),
    url(r'^users/api-token-auth$', rest_views.obtain_auth_token),

    url(r'^v2/pheno_reports', include('pheno.urls')),
    url(r'^v2/gene_weights', include('gene_weights.urls')),
    url(r'^v2/families', include('families.urls')),
)

urlpatterns = format_suffix_patterns(urlpatterns)
