import itertools
from collections import OrderedDict
import pandas as pd
from pheno.pheno_db import Instrument
from pheno.pheno_db import Measure
from pheno.common import MeasureType, Role, Gender, Status
from tools.get_pheno_property import GENERIC_PHENO_DATA_COLUMNS


def populate_instruments():
    all_instruments = OrderedDict()
    all_measures = OrderedDict()

    for instrument_name in INSTRUMENT_NAMES:
        measures = OrderedDict()
        measures_df = pd.DataFrame(
            MEASURES[instrument_name], columns=MEASURE_COLUMNS
        )
        for row in measures_df.to_dict("records"):
            m = Measure._from_dict(row)
            measures[m.measure_id] = m
            all_measures[m.measure_id] = m

        instrument = Instrument(instrument_name)
        instrument.measures = measures
        all_instruments[instrument.instrument_name] = instrument

    return all_instruments, all_measures


DBS_HEADER = GENERIC_PHENO_DATA_COLUMNS["listDatabases"][:]
INSTRUMENTS_HEADER = GENERIC_PHENO_DATA_COLUMNS["listInstruments"][:]
MEASURES_HEADER = GENERIC_PHENO_DATA_COLUMNS["listMeasures"][:]
PEOPLE_HEADER = GENERIC_PHENO_DATA_COLUMNS["listPeople"][:]

M = "i1.m1"
DB = "DB1"
DBS = [DB, "spark", "vip", "agre", "ssc"]

INSTRUMENT_NAMES = ["i1", "i2", "i3"]

MEASURE_COLUMNS = [
    "measure_name",
    "measure_id",
    "measure_type",
    "instrument_name",
    "description",
    "default_filter",
    "values_domain",
    "min_value",
    "max_value",
]

i1_measures = [
    ["m1", "i1.m1", MeasureType.continuous, "i1", "", "", "", 0, 5],
    ["m2", "i1.m2", MeasureType.categorical, "i1", "", "", "", "sad", "happy"],
]
i2_measures = [
    ["m3", "i2.m3", MeasureType.ordinal, "i2", "", "", "", 0, 0],
    ["m4", "i2.m4", MeasureType.ordinal, "i2", "", "", "", 0, 0],
    ["m5", "i2.m5", MeasureType.ordinal, "i2", "", "", "", 0, 100],
]
i3_measures = [
    ["m6", "i3.m6", MeasureType.raw, "i3", "", "", "", ".", ".."],
    ["m1", "i3.m1", MeasureType.raw, "i3", "", "", "", 0, 5],
]

MEASURES = {"i1": i1_measures, "i2": i2_measures, "i3": i3_measures}

MEASURE_ROWS = {
    m[1]: [DB, m[1], m[0], m[3], m[2].name, str(m[-2]), str(m[-1])]
    for m in itertools.chain(*MEASURES.values())
}


def get_people(measures):
    people_df = pd.DataFrame(
        [
            ["SP0000001", "SF0033601", Role.prb, Gender.F, Status.affected],
            ["SP0000002", "SF0033601", Role.sib, Gender.M, Status.unaffected],
        ],
        columns=["person_id", "family_id", "role", "gender", "status"],
    )

    for measure in measures.split(","):
        people_df[measure] = 0

    return people_df


def get_people_filtered(measures):
    people_df = pd.DataFrame(
        [["SP0000001", "SF0033601", Role.prb, Gender.F, Status.affected]],
        columns=["person_id", "family_id", "role", "gender", "status"],
    )

    for measure in measures.split(","):
        people_df[measure] = 0
    return people_df
