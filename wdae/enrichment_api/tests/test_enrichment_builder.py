from __future__ import unicode_literals


def test_build(db, enrichment_builder):
    assert enrichment_builder
    build = enrichment_builder.build()

    assert build
    assert len(build) == 2

    assert sorted([b['peopleGroupValue'] for b in build]) == \
        sorted(['autism', 'unaffected'])


def test_build_people_group_selector(db, enrichment_builder, f1_trio):
    assert enrichment_builder
    people_group = f1_trio.config.people_group_config.\
        get_people_group('phenotype')
    build = enrichment_builder.build_people_group_selector(
        ['missense'], people_group, 'autism')

    assert build
    assert len(build['childrenStats']) == 2
    assert build['childrenStats']['M'] == 1
    assert build['childrenStats']['F'] == 1
    assert build['selector'] == 'autism'
    assert build['geneSymbols'] == ['SAMD11', 'PLEKHN1', 'POGZ']
    assert build['peopleGroupId'] == 'phenotype'
    assert build['peopleGroupValue'] == 'autism'
    assert build['datasetId'] == 'f1_trio'
    assert build['missense']['all'].expected == 2
    assert build['missense']['rec'].expected == 1
    assert build['missense']['male'].expected == 1
    assert build['missense']['female'].expected == 1
