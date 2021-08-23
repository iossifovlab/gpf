from dae.genomic_resources.score_resources import NPScoreResource, \
    PositionScoreResource


def test_np_score_resource_type(test_grdb):

    resource = test_grdb.get_resource("hg19/MPC")
    assert resource is not None
    assert resource.get_id() == "hg19/MPC"

    assert isinstance(resource, NPScoreResource)


def test_position_score_resource_type(test_grdb):

    resource = test_grdb.get_resource("hg19/phastCons100")
    assert resource is not None
    assert resource.get_id() == "hg19/phastCons100"

    assert isinstance(resource, PositionScoreResource)


def test_group_resource_children(genomic_group):
    g1 = genomic_group

    print(g1.resource_children())

    children = g1.resource_children()

    assert len(children) == 1
    groups = children[0][0]
    res = children[0][1]

    assert res.get_id() == "a/b/c/d"
    assert len(groups) == 3


def test_group_resources(genomic_group):
    g1 = genomic_group
    print(g1.get_resources())

    assert len(g1.get_children()) == 1
    print(g1.get_children(deep=True))


def test_group_get_resource(genomic_group):
    assert genomic_group.get_id() == "a"

    res = genomic_group.get_resource("a/b")
    assert res is not None
    assert res.get_id() == "a/b"

    res = genomic_group.get_resource("a/b/c")
    assert res is not None
    assert res.get_id() == "a/b/c"

    res = genomic_group.get_resource("a/b/c/d")
    assert res is not None
    assert res.get_id() == "a/b/c/d"

    res = genomic_group.get_resource("d")
    assert res is None


def test_root_group_get_resource(root_group):

    assert root_group.get_id() == ""

    res = root_group.get_resource("a/b")
    assert res is not None
    assert res.get_id() == "a/b"

    res = root_group.get_resource("a/b/c")
    assert res is not None
    assert res.get_id() == "a/b/c"

    res = root_group.get_resource("a/b/c/d")
    assert res is None


def test_root_group_get_resource_not_deep(root_group):

    assert root_group.get_id() == ""

    res = root_group.get_resource("a", deep=False)
    assert res is not None
    assert res.get_id() == "a"

    res = root_group.get_resource("a/b", deep=False)
    assert res is None

    res = root_group.get_resource("a/b", deep=True)
    assert res is not None
    assert res.get_id() == "a/b"
