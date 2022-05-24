"""
Created on Jul 25, 2017

@author: lubo
"""
import os
from dae.pheno.prepare.pheno_prepare import PreparePersons, PrepareVariables
from dae.pheno.pheno_db import PhenotypeStudy
from dae.pedigrees.loader import FamiliesLoader
import pytest


@pytest.fixture(scope="session")
def instrument_files():
    return [
        os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            "fixtures/instruments/i1.csv",
        ),
        os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            "fixtures/instruments2/i1.csv",
        ),
    ]


def test_ped_prepare_simple(test_config, fake_ped_file):
    test_config.person.role.mapping = "INTERNAL"
    prep = PreparePersons(test_config)
    ped_df = FamiliesLoader.flexible_pedigree_read(fake_ped_file)

    assert ped_df is not None

    ped_df = prep.prepare_pedigree(ped_df)
    prep.save_pedigree(ped_df)


@pytest.mark.parametrize("instrument_sel", [([0, 0]), ([0, 1])])
def test_ped_prepare_variable(
    test_config, temp_dbfile, instrument_files, instrument_sel, fake_ped_file
):
    test_config.person.role.mapping = "INTERNAL"
    prep = PrepareVariables(test_config)
    assert prep is not None

    ped_df = prep.build_pedigree(fake_ped_file)
    assert ped_df is not None

    instruments = instrument_files[instrument_sel[0]: instrument_sel[1] + 1]

    df = prep.load_instrument("i1", instruments)
    df = prep.build_instrument("i1", df)
    assert df is not None
    assert len(df) == 195 * len(instruments)


def test_load_invalid_descriptions(invalid_descriptions):
    with pytest.raises(AssertionError):
        PrepareVariables.load_descriptions(invalid_descriptions)


def test_load_descriptionsc(valid_descriptions):
    descriptions = PrepareVariables.load_descriptions(valid_descriptions)
    assert descriptions("i1", "m1") == "Measure number one"
    assert descriptions("i1", "m2") == "Measure number two"
    assert descriptions("i1", "m9") == "Measure number nine"


def test_ped_prepare_variable_with_descriptions(
    test_config,
    temp_dbfile,
    instrument_files,
    fake_ped_file,
    valid_descriptions,
):
    test_config.person.role.mapping = "INTERNAL"
    prep = PrepareVariables(test_config)
    assert prep is not None

    ped_df = prep.build_pedigree(fake_ped_file)
    assert ped_df is not None

    descriptions = PrepareVariables.load_descriptions(valid_descriptions)
    df = prep.load_instrument("i1", instrument_files[0:1])
    df = prep.build_instrument("i1", df, descriptions)
    assert df is not None
    assert len(df) == 195

    temp_db = PhenotypeStudy("temp_db", temp_dbfile)
    measures = temp_db.get_measures()
    assert measures["i1.m1"].description == "Measure number one"
    assert measures["i1.m2"].description == "Measure number two"
    assert measures["i1.m9"].description == "Measure number nine"
