#!/usr/bin/env python2.7
import os
from pheno_browser.prepare_data import PreparePhenoBrowserBase
from pheno_browser.db import DbManager
from pheno.pheno_regression import PhenoRegression


from DAE import pheno # @IgnorePep8


def main():
    output_folder = './output'
    db_name = 'sqlite.db'
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    pheno_name = 'spark'

    pheno_db = pheno.get_pheno_db(pheno_name)
    pheno_regression = PhenoRegression.build_from_config(pheno_name)

    drawer = PreparePhenoBrowserBase(pheno_name, pheno_db, pheno_regression, output_folder)

    db = DbManager(dbfile=os.path.join(output_folder, db_name))
    db.build()

    # instrument = drawer.pheno_db.instruments['individuals']
    # instrument2 = drawer.pheno_db.instruments['basic_medical_screening']
    instrument3 = drawer.pheno_db.instruments['basic_medical_screening']

    # drawer.handle_measure(instrument.measures['age_at_registration_years'])
    # drawer.handle_measure(instrument.measures['diagnosis'])
    # drawer.handle_measure(instrument2.measures['age_at_eval_years'])

    drawer.handle_measure(instrument3.measures['asd'])

    # drawer.handle_measure(instrument.measures['status'])

    # ordinal = {measure.measure_type for instrument in drawer.pheno_db.instruments.values()
    #            for measure in instrument.measures.values()}
    # print(ordinal)

    # draw_ordinal_measure(
    #     instrument.measures['q18_physical_illness'], db, drawer
    # )


if __name__ == '__main__':
    main()
