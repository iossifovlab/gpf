from dae.studies.genotype_browser_config_parser import \
    GenotypeBrowserConfigParser


def test_genotype_browser_parse_variables():
    assert GenotypeBrowserConfigParser.SECTION == 'genotypeBrowser'
    assert GenotypeBrowserConfigParser.CAST_TO_BOOL == (
        'hasPresentInParent', 'hasComplex', 'hasPresentInChild',
        'hasPedigreeSelector', 'hasCNV', 'hasFamilyFilters', 'hasStudyTypes',
        'hasStudyFilters', 'hasPresentInRole', 'hasGraphicalPreview',
    )
    assert GenotypeBrowserConfigParser.SPLIT_STR_LISTS == [
        'baseColumns', 'basePreviewColumns', 'baseDownloadColumns',
        'previewColumns', 'downloadColumns', 'selectedPhenoValues',
        'familyFilters', 'selectedPhenoFiltersValues',
        'selectedGenotypeValues', 'selectedInRolesValues',
        'selectedPresentInRoleValues', 'roles', 'columns',
    ]
    assert GenotypeBrowserConfigParser.FILTER_SELECTORS == {
        'phenoFilters': 'selectedPhenoFiltersValues',
        'pheno': 'selectedPhenoValues',
        'genotype': 'selectedGenotypeValues',
        'inRoles': 'selectedInRolesValues',
        'presentInRole': 'selectedPresentInRoleValues'
    }


def test_get_description_keys():
    assert GenotypeBrowserConfigParser._get_description_keys() == [
        'hasPedigreeSelector', 'hasPresentInChild', 'hasPresentInParent',
        'hasPresentInRole', 'hasCNV', 'hasComplex', 'hasFamilyFilters',
        'hasStudyFilters', 'hasStudyTypes', 'hasGraphicalPreview',
        'previewColumns', 'rolesFilterOptions', 'genotypeColumns',
        'phenoFilters', 'familyFilters', 'presentInRole', 'phenoColumns',
        'downloadColumns'
    ]


def test_get_config_description(quads_f1_config):
    description = GenotypeBrowserConfigParser.get_config_description(
        quads_f1_config.genotype_browser_config
    )

    assert len(description) == \
        len(GenotypeBrowserConfigParser._get_description_keys())

    for key in description.keys():
        assert description[key] == quads_f1_config.genotype_browser_config[key]
