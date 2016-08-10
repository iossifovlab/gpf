from django.conf.urls import patterns, url
from rest_framework.urlpatterns import format_suffix_patterns

from api.sd.views import SequencingDenovoPreview, SequencingDenovoDownload
from api.ssc.views import SSCPreview, SSCDownload
from enrichment.views import EnrichmentView
from reports.views import VariantReportsView, FamiliesDataDownloadView


urlpatterns = patterns(
    'api.views',
    url(r'^denovo_studies$', 'denovo_studies_list'),
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

    url(r'^reports/variant_reports/(?P<study_name>.+)$',
        VariantReportsView.as_view()),
    url(r'^reports/families_data/(?P<study_name>.+)$',
        FamiliesDataDownloadView.as_view()),

    url(r'^gene_sets$', 'gene_sets_list'),
    url(r'^gene_set_list2$', 'gene_set_list2'),
    url(r'^gene_set_download$', 'gene_set_download'),

    url(r'^study_tab_phenotypes/(?P<study_tab>.+)$', 'study_tab_phenotypes'),
    url(r'^gene_set_phenotypes$', 'gene_set_phenotypes'),

    url(r'^report_studies$', 'report_studies'),
    url(r'^enrichment_test_by_phenotype$', EnrichmentView.as_view()),
    url(r'^child_types$', 'child_type_list'),
    url(r'^studies_summaries$', 'studies_summaries'),

)

urlpatterns = format_suffix_patterns(urlpatterns)
