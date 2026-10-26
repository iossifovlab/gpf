# pylint: disable=W0621,C0114,C0116,W0212,W0613,R0903
"""Every ``QueryBaseView`` subclass has an explicit access policy."""
import importlib
from collections.abc import Iterable, Iterator, Mapping

from django.conf import settings

from query_base.query_base import QueryBaseView

PUBLIC = "public"
GATED = "gated"

# A view is ``gated`` when it checks the access to the dataset id that it
# serves, or when it requires a staff user. Every other view is ``public``.
# A view that mixes in ``DatasetAccessRightsView`` but finds no dataset id
# in the request is ``public``.
ACCESS_POLICIES: dict[str, str] = {
    # The dataset list and its metadata stay public: the Web UI lists the
    # locked datasets too.
    "datasets_api.views.DatasetView": PUBLIC,
    "datasets_api.views.VisibleDatasetsView": PUBLIC,
    "datasets_api.views.DatasetHierarchyView": PUBLIC,
    "datasets_api.views.DatasetDescriptionView": PUBLIC,
    "datasets_api.views.DatasetPedigreeView": GATED,
    # Serves only the datasets that the user may access.
    "datasets_api.views.FederationDatasetsView": PUBLIC,
    # The base class has no handler. Its subclasses require a staff user.
    "datasets_api.views.BaseDatasetPermissionsView": PUBLIC,
    "datasets_api.views.DatasetPermissionsView": GATED,
    "datasets_api.views.DatasetPermissionsSingleView": GATED,
    "person_sets_api.views.CollectionConfigsView": GATED,
    "person_sets_api.views.CollectionDomainView": GATED,
    "person_sets_api.views.CollectionStatsView": GATED,
    "common_reports_api.views.VariantReportsView": PUBLIC,
    "common_reports_api.views.VariantReportsFullView": GATED,
    "common_reports_api.views.FamilyCounterListView": GATED,
    "common_reports_api.views.FamilyCounterDownloadView": GATED,
    "common_reports_api.views.FamiliesDataDownloadView": GATED,
    "enrichment_api.views.EnrichmentModelsView": PUBLIC,
    "enrichment_api.views.EnrichmentTestView": GATED,
    "family_api.views.ListFamiliesView": GATED,
    "family_api.views.FamilyDetailsView": GATED,
    "family_api.views.ListMembersView": GATED,
    "family_api.views.MemberDetailsView": GATED,
    "family_api.views.AllMemberDetailsView": GATED,
    "family_api.views.ListAllDetailsView": GATED,
    # Mixes in ``DatasetAccessRightsView``, but names no dataset.
    "family_api.views.TagsView": PUBLIC,
    "genotype_browser.views.GenotypeBrowserQueryView": GATED,
    "genotype_browser.views.GenotypeBrowserQueryDownloadView": GATED,
    "gene_view.views.ConfigView": GATED,
    "gene_view.views.QuerySummaryVariantsView": PUBLIC,
    "gene_view.views.DownloadSummaryVariantsView": PUBLIC,
    # The Phenotype Tool stays usable on a locked dataset.
    "measures_api.views.PhenoMeasureHistogramView": PUBLIC,
    "measures_api.views.PhenoMeasureHistogramViewBeta": PUBLIC,
    "measures_api.views.PhenoDataRoleListView": PUBLIC,
    "measures_api.views.PhenoMeasuresView": PUBLIC,
    "measures_api.views.PhenoMeasureListView": PUBLIC,
    "measures_api.views.PhenoMeasureRegressionsView": PUBLIC,
    "measures_api.views.PhenoMeasurePartitionsView": GATED,
    "pheno_tool_api.views.PhenoToolView": PUBLIC,
    "pheno_tool_api.views.PhenoToolDownload": GATED,
    "pheno_tool_api.views.PhenoToolPeopleValues": GATED,
    "pheno_tool_api.views.PhenoToolMeasure": GATED,
    "pheno_tool_api.views.PhenoToolMeasures": GATED,
    "pheno_tool_api.views.PhenoToolInstruments": GATED,
    "pheno_browser_api.views.PhenoInstrumentsView": PUBLIC,
    "pheno_browser_api.views.PhenoMeasuresInfoView": PUBLIC,
    "pheno_browser_api.views.PhenoMeasureDescriptionView": PUBLIC,
    "pheno_browser_api.views.PhenoMeasuresView": PUBLIC,
    "pheno_browser_api.views.PhenoMeasuresCount": GATED,
    "pheno_browser_api.views.PhenoMeasuresDownload": GATED,
    # ``IsDatasetAllowed`` does not read the ``pheno_id`` of this view.
    "pheno_browser_api.views.PhenoImagesView": PUBLIC,
    # The routes below serve no dataset data.
    "gene_sets.views.GeneSetsCollectionsView": PUBLIC,
    "gene_sets.views.DenovoGeneSetsTypesView": PUBLIC,
    "gene_sets.views.DenovoGeneSetsDb": PUBLIC,
    "gene_sets.views.GeneSetsView": PUBLIC,
    "gene_sets.views.GeneSetDownloadView": PUBLIC,
    "gene_sets.views.GeneSetsHasDenovoView": PUBLIC,
    "gene_scores.views.GeneScoresListView": PUBLIC,
    "gene_scores.views.HistogramView": PUBLIC,
    "gene_scores.views.GeneScoresDownloadView": PUBLIC,
    "gene_scores.views.GeneScoresPartitionsView": PUBLIC,
    "gene_profiles_api.views.ConfigurationView": PUBLIC,
    "gene_profiles_api.views.ProfileView": PUBLIC,
    "gene_profiles_api.table_views.TableRowsView": PUBLIC,
    "gene_profiles_api.table_views.GeneSymbolsView": PUBLIC,
    "genomes_api.views.DefaultGeneModelsId": PUBLIC,
    "genomes_api.views.GeneModels": PUBLIC,
    "genomes_api.views.GeneSymbolsSearch": PUBLIC,
    "genomes_api.views.GeneSymbolsValidate": PUBLIC,
    "genomic_scores_api.views.GenomicScoresView": PUBLIC,
    "genomic_scores_api.views.GenomicScoreDescsView": PUBLIC,
    "gpf_instance.views.MarkdownFileView": PUBLIC,
    "gpf_instance.views.DescriptionView": PUBLIC,
    "gpf_instance.views.AboutDescriptionView": PUBLIC,
    "gpf_instance.views.GenomeView": PUBLIC,
}


def view_name(view: type) -> str:
    return f"{view.__module__}.{view.__qualname__}"


def unlisted_views(
    views: Iterable[type], policies: Mapping[str, str],
) -> list[str]:
    """Return the names of the views that have no entry in the policies."""
    return sorted(
        name for name in map(view_name, views) if name not in policies
    )


def test_unlisted_views_reports_a_view_without_a_policy() -> None:
    class Listed:
        pass

    class Unlisted:
        pass

    policies = {view_name(Listed): PUBLIC}

    assert unlisted_views([Listed, Unlisted], policies) == [
        view_name(Unlisted),
    ]


def all_subclasses(base: type) -> Iterator[type]:
    for subclass in base.__subclasses__():
        yield subclass
        yield from all_subclasses(subclass)


def query_base_views() -> set[type]:
    """Return every ``QueryBaseView`` subclass, after all views load."""
    importlib.import_module(settings.ROOT_URLCONF)
    return set(all_subclasses(QueryBaseView))


def test_every_query_base_view_has_an_access_policy() -> None:
    assert unlisted_views(query_base_views(), ACCESS_POLICIES) == []


def test_every_access_policy_names_a_query_base_view() -> None:
    names = set(map(view_name, query_base_views()))

    assert sorted(set(ACCESS_POLICIES) - names) == []


def test_access_policies_are_public_or_gated() -> None:
    assert set(ACCESS_POLICIES.values()) <= {PUBLIC, GATED}
