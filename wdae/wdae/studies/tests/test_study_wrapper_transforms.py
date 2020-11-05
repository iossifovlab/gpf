import pytest

from dae.variants.attributes import Inheritance, Role
from dae.backends.attributes_query import inheritance_query, role_query, \
    OrNode
from studies.study_wrapper import StudyWrapper


@pytest.mark.parametrize(
    "kwargs,inheritance,roles,accepted",
    [
        ({
            "presentInChild": ["proband only"],
            "presentInParent": {"presentInParent": ["neither"]},
        }, [Inheritance.denovo], [Role.prb], True),
        ({
            "presentInChild": ["proband only"],
            "presentInParent": {"presentInParent": ["neither"]},
        }, [Inheritance.denovo], [Role.sib], False),
        ({
            "presentInChild": ["proband only"],
            "presentInParent": {"presentInParent": ["neither"]},
        }, [Inheritance.mendelian], [Role.prb], False),
        ({
            "presentInChild": ["proband only", "sibling only"],
            "presentInParent": {"presentInParent": ["neither"]},
        }, [Inheritance.denovo], [Role.prb], True),
        ({
            "presentInChild": ["proband only", "sibling only"],
            "presentInParent": {"presentInParent": ["neither"]},
        }, [Inheritance.denovo], [Role.sib], True),
        ({
            "presentInChild": ["proband only", "sibling only"],
            "presentInParent": {"presentInParent": ["neither"]},
        }, [Inheritance.denovo], [Role.prb, Role.sib], False),
        ({
            "presentInChild": [
                "proband only", "sibling only", "proband and sibling"],
            "presentInParent": {"presentInParent": ["neither"]},
        }, [Inheritance.denovo], [Role.prb, Role.sib], True),
        ({
            "presentInChild": ["proband only"],
            "presentInParent": {"presentInParent": ["mother only"]},
        }, [Inheritance.mendelian], [Role.prb, Role.mom], True),
        ({
            "presentInChild": ["proband only"],
            "presentInParent": {"presentInParent": ["mother only"]},
        },
            [Inheritance.denovo, Inheritance.mendelian],
            [Role.prb, Role.mom], True),
        ({
            "presentInChild": ["neither"],
            "presentInParent": {"presentInParent": ["mother only"]},
        },
            [Inheritance.missing],
            [Role.mom], True),
    ]
)
def test_transform_present_in_child_and_present_in_parent(
        kwargs, inheritance, roles, accepted):

    StudyWrapper._transform_present_in_child_and_present_in_parent(kwargs)

    rq = kwargs.get("roles")
    assert rq is not None
    rm = role_query.transform_tree_to_matcher(rq)

    iq = kwargs.get("inheritance")
    assert iq is not None
    assert len(iq) == 1

    it = inheritance_query.transform_query_string_to_tree(iq[0])
    im = inheritance_query.transform_tree_to_matcher(it)

    # rres = rm.match(roles)
    # ires = im.match(inheritance)
    # print(rres, ires)

    if accepted:
        assert rm.match(roles) and im.match(inheritance)
    else:
        assert not (rm.match(roles) and im.match(inheritance))


def test_attributes_query_roles():
    rq = "sib and not prb"
    rt = OrNode([role_query.transform_query_string_to_tree(rq)])

    rm = role_query.transform_tree_to_matcher(rt)

    result = rm.match([Role.prb])
    assert not result

# @pytest.mark.parametrize(
#     "option,count",
#     [
#         ({"presentInParent": ["mother only"]}, 1),
#         ({"presentInParent": ["father only"]}, 1),
#         ({"presentInParent": ["mother and father"]}, 1),
#         ({"presentInParent": ["neither"]}, 1),
#         ({"presentInParent": ["mother and father", "mother only"]}, 2),
#         ({"presentInParent": ["mother only", "neither"]}, 2),
#         (
#             {
#                 "presentInParent": [
#                     "mother only",
#                     "father only",
#                     "mother and father",
#                     "neither",
#                 ]
#             },
#             4,
#         ),
#     ],
#     ids=repr,
# )
# def test_transform_present_in_parent(option, count, quads_in_parent_wrapper):
#     variants = list(
#         quads_in_parent_wrapper.query_variants(presentInParent=option)
#     )

#     assert len(variants) == count
