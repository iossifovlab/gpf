#!/usr/bin/env python2.7
import os
from pheno_browser.prepare_data import PreparePhenoBrowserBase
from pheno_browser.db import DbManager
# from DAE import pheno # @IgnorePep8


def create_measure_object(measure):
    return {
        'measure_id': measure.measure_id,
        'instrument_name': measure.instrument_name,
        'measure_name': measure.measure_name,
        'measure_type': measure.measure_type,
        'values_domain': measure.values_domain
    }


def draw_continuous_measure(measure, db, drawer):
    assert measure.measure_type == "continuous"
    measure_object = create_measure_object(measure)

    drawer.build_values_violinplot(measure, measure_object)
    db.save(measure_object)


def draw_categorical_measure(measure, db, drawer):
    assert measure.measure_type == "categorical"
    measure_object = create_measure_object(measure)

    drawer.build_values_categorical_distribution(measure, measure_object)
    db.save(measure_object)


def draw_ordinal_measure(measure, db, drawer):
    print(measure.measure_type)
    assert measure.measure_type == "ordinal"
    measure_object = create_measure_object(measure)

    drawer.build_values_ordinal_distribution(measure, measure_object)
    db.save(measure_object)


def main():
    output_folder = './output'
    db_name = 'sqlite.db'
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    drawer = PreparePhenoBrowserBase('spark', output_folder)

    db = DbManager(dbfile=os.path.join(output_folder, db_name))
    db.build()

    instrument = drawer.pheno_db.instruments['individuals']
    draw_continuous_measure(
        instrument.measures['age_at_registration_years'], db, drawer
    )

    draw_categorical_measure(
        instrument.measures['diagnosis'], db, drawer
    )

    # ordinal = {measure.measure_type for instrument in drawer.pheno_db.instruments.values()
    #            for measure in instrument.measures.values()}
    # print(ordinal)

    # draw_ordinal_measure(
    #     instrument.measures['q18_physical_illness'], db, drawer
    # )


if __name__ == '__main__':
    main()
