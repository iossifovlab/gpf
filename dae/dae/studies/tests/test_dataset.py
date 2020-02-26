

def test_inheritance_trio_can_init(inheritance_trio_genotype_data_group):
    print("is inited")
    assert inheritance_trio_genotype_data_group is not None


def test_inheritance_trio_description(inheritance_trio_genotype_data_group):
    assert inheritance_trio_genotype_data_group.description == \
        "Sample description in markdown format.\n"
