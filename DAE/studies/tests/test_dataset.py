

def test_inheritance_trio_can_init(inheritance_trio_dataset):
    print("is inited")
    assert inheritance_trio_dataset is not None


def test_inheritance_trio_description(inheritance_trio_dataset):
    assert inheritance_trio_dataset.description == \
           "Sample description in markdown format.\n"
