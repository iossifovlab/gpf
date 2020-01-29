import pytest
from box import Box
from dae.studies.genotype_browser_config_parser import \
    GenotypeBrowserConfigParser, verify_inheritance_types


pytestmark = pytest.mark.skip


def test_genotype_browser_parse_variables():
    assert GenotypeBrowserConfigParser.SECTION == 'genotypeBrowser'
    assert GenotypeBrowserConfigParser.CAST_TO_BOOL == (
        'hasPresentInParent', 'hasComplex', 'hasPresentInChild',
        'hasPedigreeSelector', 'hasCNV', 'hasFamilyFilters', 'hasStudyTypes',
        'hasStudyFilters', 'hasPresentInRole', 'hasGraphicalPreview',
    )
    assert GenotypeBrowserConfigParser.SPLIT_STR_LISTS == [
        'previewColumns',
        'downloadColumns',
        'selectedPhenoColumnValues',
        'familyFilters',
        'selectedPhenoFiltersValues',
        'selectedGenotypeColumnValues',
        'selectedInRolesValues',
        'selectedPresentInRoleValues',
        'inheritanceTypeFilter',
        'selectedInheritanceTypeFilterValues',
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
        'previewColumns', 'genotypeColumns', 'phenoFilters', 'familyFilters',
        'presentInRole', 'downloadColumns', 'inheritanceTypeFilter',
        'selectedInheritanceTypeFilterValues',
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


def test_inheritance_types_selected_without_available():
    genotype_browser_config = {
        'genotypeBrowser': {
            'selectedInheritanceTypeFilterValues': 'denovo, reference'
        }
    }
    genotype_browser_config = Box(
        genotype_browser_config, camel_killer_box=True,
        default_box=True, default_box_attr=None
    )

    with pytest.raises(AssertionError) as _:
        GenotypeBrowserConfigParser.parse(genotype_browser_config)


def test_inheritance_types_selecting_nonavailable_filters():
    genotype_browser_config = {
        'genotypeBrowser': {
            'inheritanceTypeFilter': 'mendelian, denovo',
            'selectedInheritanceTypeFilterValues': 'denovo, reference'
        }
    }
    genotype_browser_config = Box(
        genotype_browser_config, camel_killer_box=True,
        default_box=True, default_box_attr=None
    )

    with pytest.raises(AssertionError) as _:
        GenotypeBrowserConfigParser.parse(genotype_browser_config)
