import pytest
from dae.studies.genotype_browser_config_parser import \
    GenotypeBrowserConfigParser, verify_inheritance_types


def test_genotype_browser_parse_variables():
    assert GenotypeBrowserConfigParser.SECTION == 'genotypeBrowser'
    assert GenotypeBrowserConfigParser.CAST_TO_BOOL == (
        'hasPresentInParent', 'hasComplex', 'hasPresentInChild',
        'hasPedigreeSelector', 'hasCNV', 'hasFamilyFilters', 'hasStudyTypes',
        'hasStudyFilters', 'hasPresentInRole', 'hasGraphicalPreview',
    )
    assert GenotypeBrowserConfigParser.SPLIT_STR_LISTS == [
        'baseColumns', 'basePreviewColumns', 'baseDownloadColumns',
        'previewColumns', 'downloadColumns', 'selectedPhenoColumnValues',
        'familyFilters', 'selectedPhenoFiltersValues',
        'selectedGenotypeColumnValues', 'selectedInRolesValues',
        'selectedPresentInRoleValues', 'roles', 'columns',
        'inheritanceTypeFilter', 'selectedInheritanceTypeFilterValues',
    ]
    assert GenotypeBrowserConfigParser.FILTER_SELECTORS == {
        'phenoFilters': 'selectedPhenoFiltersValues',
        'pheno': 'selectedPhenoColumnValues',
        'genotype': 'selectedGenotypeColumnValues',
        'inRoles': 'selectedInRolesValues',
        'presentInRole': 'selectedPresentInRoleValues'
    }

    assert GenotypeBrowserConfigParser.VERIFY_VALUES == {
        'inheritanceTypeFilter': verify_inheritance_types,
        'selectedInheritanceTypeFilterValues': verify_inheritance_types
    }


def test_get_description_keys():
    assert GenotypeBrowserConfigParser._get_description_keys() == [
        'hasPedigreeSelector', 'hasPresentInChild', 'hasPresentInParent',
        'hasPresentInRole', 'hasCNV', 'hasComplex', 'hasFamilyFilters',
        'hasStudyFilters', 'hasStudyTypes', 'hasGraphicalPreview',
        'previewColumns', 'rolesFilterOptions', 'genotypeColumns',
        'phenoFilters', 'familyFilters', 'presentInRole', 'downloadColumns',
        'inheritanceTypeFilter', 'selectedInheritanceTypeFilterValues',
    ]


def test_get_config_description(quads_f1_config):
    description = GenotypeBrowserConfigParser.get_config_description(
        quads_f1_config.genotype_browser_config
    )

    assert len(description) == \
        len(GenotypeBrowserConfigParser._get_description_keys())

    for key in description.keys():
        assert description[key] == quads_f1_config.genotype_browser_config[key]


def test_inheritance_types_validation():
    assert verify_inheritance_types(['mendelian', 'denovo']) == \
        ['mendelian', 'denovo']
    with pytest.raises(AssertionError) as excinfo:
        verify_inheritance_types(['mendelian', 'nonexistent', 'denovo'])
    assert str(excinfo.value) == 'Inheritance type nonexistent does not exist!'
