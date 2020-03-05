from dae.common_reports.people_filters import MultiFilter
from dae.common_reports.people_filters import FilterCollection


def test_filter(filter_role):
    assert filter_role.people_group.id == "role"
    assert filter_role.specified_value == "mom"
    assert filter_role.filter_name == "Mother"


def test_filter_object(filter_object, filter_role, filter_people_group):
    # filter_object_from_list = FilterObject.from_list(
    #     [[filter_role]])

    assert filter_object.filter_name == "Mother"
    filter_object.add_filter(filter_people_group)

    assert filter_object.filter_name == "Mother and Pheno"

    # assert len(filter_object_from_list) == 1
    # assert len(filter_object_from_list[0].filters) == \
    #     len(filter_object.filters)


def test_filter_objects(filter_object, filter_people_group):
    filter_objects = FilterCollection("Test", filters=[filter_object])

    assert filter_objects.get_filter_names() == ["Mother"]
    assert filter_objects.get_filter_by_name("Mother") is not None
    assert filter_objects.get_filter_by_name("Mother").filter_name == "Mother"
    assert filter_objects.get_filter_by_name("mom and dad") is None

    filter_objects.add_filter(MultiFilter([filter_people_group]))

    assert filter_objects.get_filter_names() == ["Mother", "Pheno"]


def test_get_filter_objects(filter_objects):
    assert len(filter_objects) == 1
    assert filter_objects[0].name == "Role and Diagnosis"
    assert len(filter_objects[0].filters) == 16
    assert sorted(filter_objects[0].get_filter_names()) == sorted(
        [
            "mom and unknown",
            "mom and phenotype1",
            "mom and phenotype2",
            "mom and unaffected",
            "sib and unknown",
            "sib and phenotype1",
            "sib and phenotype2",
            "sib and unaffected",
            "dad and unknown",
            "dad and phenotype1",
            "dad and phenotype2",
            "dad and unaffected",
            "prb and unknown",
            "prb and phenotype1",
            "prb and phenotype2",
            "prb and unaffected",
        ]
    )
