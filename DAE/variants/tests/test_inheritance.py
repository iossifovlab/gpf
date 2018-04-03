'''
Created on Feb 27, 2018

@author: lubo
'''
from variants.attributes import Inheritance
from variants.variant import FamilyVariant as FV


def test_combine_inherits_unknown():

    assert Inheritance.unknown == \
        FV.combine_inheritance(
            Inheritance.unknown,
        )

    assert Inheritance.unknown == \
        FV.combine_inheritance(
            Inheritance.unknown,
            Inheritance.mendelian,
        )

    assert Inheritance.unknown == \
        FV.combine_inheritance(
            Inheritance.denovo,
            Inheritance.omission,
            Inheritance.unknown,
            Inheritance.mendelian,
        )

    assert Inheritance.unknown == \
        FV.combine_inheritance(
            Inheritance.denovo,
            Inheritance.omission,
            Inheritance.other,
            Inheritance.unknown,
            Inheritance.mendelian,
        )

    assert Inheritance.unknown == \
        FV.combine_inheritance(
            Inheritance.denovo,
            Inheritance.omission,
            Inheritance.other,
            Inheritance.mendelian,
        )


def test_combine_inherits_mendelian():

    assert Inheritance.mendelian == \
        FV.combine_inheritance(
            Inheritance.mendelian,
        )

    assert Inheritance.mendelian == \
        FV.combine_inheritance(
            Inheritance.mendelian,
            Inheritance.mendelian,
        )

    assert Inheritance.mendelian != \
        FV.combine_inheritance(
            Inheritance.denovo,
            Inheritance.omission,
            Inheritance.mendelian,
            Inheritance.mendelian,
        )

    assert Inheritance.mendelian != \
        FV.combine_inheritance(
            Inheritance.denovo,
            Inheritance.omission,
            Inheritance.other,
            Inheritance.mendelian,
        )


def test_combine_inherits_denovo():

    assert Inheritance.denovo == \
        FV.combine_inheritance(
            Inheritance.denovo,
        )

    assert Inheritance.denovo == \
        FV.combine_inheritance(
            Inheritance.denovo,
            Inheritance.mendelian,
        )

    assert Inheritance.denovo == \
        FV.combine_inheritance(
            Inheritance.mendelian,
            Inheritance.denovo,
            Inheritance.mendelian,
        )


def test_combine_inherits_omission():

    assert Inheritance.omission == \
        FV.combine_inheritance(
            Inheritance.omission,
        )

    assert Inheritance.omission == \
        FV.combine_inheritance(
            Inheritance.omission,
            Inheritance.mendelian,
        )

    assert Inheritance.omission == \
        FV.combine_inheritance(
            Inheritance.mendelian,
            Inheritance.omission,
            Inheritance.mendelian,
        )


def test_combine_inherits_other():

    assert Inheritance.other == \
        FV.combine_inheritance(
            Inheritance.omission,
            Inheritance.denovo,
        )

    assert Inheritance.other == \
        FV.combine_inheritance(
            Inheritance.omission,
            Inheritance.mendelian,
            Inheritance.denovo,
        )

    assert Inheritance.other == \
        FV.combine_inheritance(
            Inheritance.mendelian,
            Inheritance.omission,
            Inheritance.denovo,
            Inheritance.mendelian,
        )
