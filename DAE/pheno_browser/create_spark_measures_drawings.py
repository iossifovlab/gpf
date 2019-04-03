#!/usr/bin/env python

from __future__ import unicode_literals
import os
from pheno_browser.prepare_data import PreparePhenoBrowserBase


from DAE import pheno
from pheno.pheno_regression import PhenoRegression


def main():
    output_folder = './output'
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    pheno_name = 'spark'

    pheno_db = pheno.get_pheno_db(pheno_name)
    pheno_regression = PhenoRegression.build_from_config(pheno_name)

    drawer = PreparePhenoBrowserBase(
        pheno_name, pheno_db, pheno_regression, output_folder)

    pheno_db = pheno.get_pheno_db(pheno_name)
    pheno_regression = PhenoRegression.build_from_config(pheno_name)

    drawer = PreparePhenoBrowserBase(
        pheno_name, pheno_db, pheno_regression, output_folder)

    # db.build()

    # instrument = drawer.pheno_db.instruments['individuals']
    # instrument2 = drawer.pheno_db.instruments['basic_medical_screening']
    instrument3 = drawer.pheno_db.instruments['basic_medical_screening']

    # drawer.handle_measure(instrument.measures['age_at_registration_years'])
    # drawer.handle_measure(instrument.measures['diagnosis'])
    # drawer.handle_measure(instrument2.measures['age_at_eval_years'])

    drawer.handle_measure(instrument3.measures['asd'])

    # drawer.handle_measure(instrument.measures['status'])

    # ordinal = {
    #       measure.measure_type
    #       for instrument in drawer.pheno_db.instruments.values()
    #       for measure in instrument.measures.values()}
    # print(ordinal)

    # draw_ordinal_measure(
    #     instrument.measures['q18_physical_illness'], db, drawer
    # )


if __name__ == '__main__':
    main()
