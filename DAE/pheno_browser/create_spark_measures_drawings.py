#!/usr/bin/env python2.7
import os
from pheno_browser.prepare_data import PreparePhenoBrowserBase
from pheno_browser.db import DbManager


# from DAE import pheno # @IgnorePep8


def main():
    output_folder = './output'
    db_name = 'sqlite.db'
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    drawer = PreparePhenoBrowserBase('spark', output_folder)

    db = DbManager(dbfile=os.path.join(output_folder, db_name))
    db.build()

    instrument = drawer.pheno_db.instruments['individuals']
    instrument2 = drawer.pheno_db.instruments['basic_medical_screening']

    # drawer.handle_measure(instrument.measures['age_at_registration_years'])
    # drawer.handle_measure(instrument.measures['diagnosis'])
    # drawer.handle_measure(instrument2.measures['age_at_eval_years'])
    drawer.handle_measure(instrument2.measures['birth_def_urogen_uter_agen'])

    # drawer.handle_measure(instrument.measures['status'])

    # ordinal = {measure.measure_type for instrument in drawer.pheno_db.instruments.values()
    #            for measure in instrument.measures.values()}
    # print(ordinal)

    # draw_ordinal_measure(
    #     instrument.measures['q18_physical_illness'], db, drawer
    # )


if __name__ == '__main__':
    main()
