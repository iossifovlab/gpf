from dae.common_reports.filter import FilterObject, FilterObjects


def test_filter(filter_role):
    assert filter_role.column == 'role'
    assert filter_role.value == 'mom'
    assert filter_role.column_value == 'Mother'

    assert filter_role.get_column_name() == 'Mother'


def test_filter_object(filter_object, filter_role, filter_people_group):
    filter_object_from_list = FilterObject.from_list(
        [[filter_role, filter_people_group]])

    assert filter_object.get_column_name() == 'Mother'
    filter_object.add_filter(
        filter_people_group.column, filter_people_group.value,
        filter_people_group.column_value)
    assert filter_object.get_column_name() == 'Mother and Pheno'

    assert len(filter_object_from_list) == 1
    assert len(filter_object_from_list[0].filters) == \
        len(filter_object.filters)


def test_filter_objects(filter_object, filter_people_group):
    filter_objects = FilterObjects('Role', filter_objects=[filter_object])

    assert filter_objects.name == 'Role'
    assert filter_objects.get_columns() == ['Mother']
    assert filter_objects.get_filter_object_by_column_name(
        'Mother') is not None
    assert filter_objects.get_filter_object_by_column_name(
        'Mother').get_column_name() == 'Mother'
    assert filter_objects.get_filter_object_by_column_name(
        'mom and dad') is None

    filter_objects.add_filter_object(filter_people_group)

    assert filter_objects.get_columns() == ['Mother', 'Pheno']


def test_get_filter_objects(filter_objects):
    assert len(filter_objects) == 1
    assert filter_objects[0].name == 'Role and Diagnosis'
    assert len(filter_objects[0].filter_objects) == 16
    assert sorted(filter_objects[0].get_columns()) == sorted([
        'mom and unknown', 'mom and phenotype1', 'mom and phenotype2',
        'mom and unaffected', 'sib and unknown', 'sib and phenotype1',
        'sib and phenotype2', 'sib and unaffected', 'dad and unknown',
        'dad and phenotype1', 'dad and phenotype2', 'dad and unaffected',
        'prb and unknown', 'prb and phenotype1', 'prb and phenotype2',
        'prb and unaffected'
    ])
