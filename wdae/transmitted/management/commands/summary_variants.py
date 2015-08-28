'''
Created on Aug 28, 2015

@author: lubo
'''
from django.core.management.base import BaseCommand, CommandError
from DAE import vDB
import gzip
from transmitted.models import SummaryVariant
from VariantsDB import Variant


class Command(BaseCommand):
    args = '<study_name>'
    help = '''Importst summary variants from transmitted study <study_name>
    into the SQL database.'''

    @staticmethod
    def safe_float(s):
        if s.strip() == '':
            return float('NaN')
        else:
            return float(s)

    def get_summary_filename(self, study_name):
        study = vDB.get_study(study_name)

        summary_filename = study.vdb._config.get(
            study._configSection,
            'transmittedVariants.indexFile') + ".txt.bgz"
        return summary_filename

    def create_summary_variant(self, vals):
        vals["location"] = vals["chr"] + ":" + vals["position"]
        v = Variant(vals)
        v.study = self.study
        if self.summary_row['n_alt_alls'] == 1:
            v.popType = 'ultraRare'
        else:
            v.popType = 'common'
        return v

    def handle(self, *args, **options):
        if(len(args) != 1):
            raise CommandError('Exactly one argument expected')

        study_name = args[0]
        print("Working with transmitted study: {}".format(study_name))

        summary_filename = self.get_summary_filename(study_name)
        with gzip.open(summary_filename, 'r') as fh:
            column_names = fh.readline().rstrip().split('\t')
            nrow = 0
            for line in fh:
                data = line.strip("\r\n").split("\t")
                vals = dict(zip(column_names, data))
                sv = SummaryVariant.objects.create(
                    ln=nrow,
                    chrome=vals['chr'],
                    position=int(vals['position']),
                    variant=vals['variant'],
                    variant_type=vals['variant'][:3],
                    # effect_type=vals['effectType'],
                    n_par_called=int(vals['all.nParCalled']),
                    n_alt_alls=int(vals['all.nAltAlls']),
                    alt_freq=float(vals['all.altFreq']),

                    prcnt_par_called=float(vals['all.prcntParCalled']),
                    seg_dups=int(vals['segDups']),
                    hw=float(vals['HW']),

                    ssc_freq=self.safe_float(vals['SSC-freq']),
                    evs_freq=self.safe_float(vals['EVS-freq']),
                    e65_freq=self.safe_float(vals['E65-freq']),
                )
                sv.save()
                nrow += 1
                if nrow % 100 == 0:
                    print("line: {}".format(nrow))
