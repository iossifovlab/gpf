'''
Created on Aug 28, 2015

@author: lubo
'''
from django.core.management.base import BaseCommand, CommandError
from DAE import vDB
import gzip
from transmitted.models import SummaryVariant, GeneEffectVariant, FamilyVariant
from VariantsDB import Variant, parseGeneEffect
import copy


class Command(BaseCommand):
    args = '<study_name>'
    help = '''Importst summary variants from transmitted study <study_name>
    into the SQL database.'''

    @staticmethod
    def safe_float(s):
        if s.strip() == '':
            return None
        else:
            return float(s)

    def get_study_filenames(self, study_name):
        study = vDB.get_study(study_name)
        self.study = study

        summary_filename = study.vdb._config.get(
            study._configSection,
            'transmittedVariants.indexFile') + ".txt.bgz"
        tm_filename = study.vdb._config.get(
            study._configSection,
            'transmittedVariants.indexFile') + "-TOOMANY.txt.bgz"
        return (summary_filename, tm_filename)

    def create_summary_variant(self, vals):
        vals["location"] = vals["chr"] + ":" + vals["position"]
        v = Variant(vals)
        v.study = self.study
        if int(vals['all.nAltAlls']) == 1:
            v.popType = 'ultraRare'
        else:
            v.popType = 'common'
        return v

    def create_summary_variant_dict(self, nrow, vals, evvals):
        res = {
            'ln': nrow,
            'chrome': vals['chr'],
            'position': int(vals['position']),
            'variant': vals['variant'],
            'variant_type': vals['variant'][:3],
            'effect_type': evvals[0]['effect_type'] if evvals else None,
            'effect_gene': evvals[0]['symbol'] if evvals else None,
            'effect_count': len(evvals),
            'n_par_called': int(vals['all.nParCalled']),
            'n_alt_alls': int(vals['all.nAltAlls']),
            'alt_freq': float(vals['all.altFreq']),
            'prcnt_par_called': float(vals['all.prcntParCalled']),
            'seg_dups': int(vals['segDups']),
            'hw': float(vals['HW']),
            'ssc_freq': self.safe_float(vals['SSC-freq']),
            'evs_freq': self.safe_float(vals['EVS-freq']),
            'e65_freq': self.safe_float(vals['E65-freq']),
        }
        return res

    def create_effect_variant_dict(self, vals):
        gene_effects = parseGeneEffect(vals['effectGene'])
        variant_type = vals['variant'][0:3]

        if len(gene_effects) == 0 and vals['effectGene'] == 'intergenic':
            return [{
                'symbol': None,
                'effect_type': 'intergenic',
                'variant_type': variant_type,
                'n_par_called': int(vals['all.nParCalled']),
                'n_alt_alls': int(vals['all.nAltAlls']),
                'alt_freq': float(vals['all.altFreq']),
            }]

        res = []
        for ge in gene_effects:
            eres = {
                'symbol': ge['sym'],
                'effect_type': ge['eff'],
                'variant_type': variant_type,
                'n_par_called': int(vals['all.nParCalled']),
                'n_alt_alls': int(vals['all.nAltAlls']),
                'alt_freq': float(vals['all.altFreq']),
            }
            res.append(eres)
        return res

    def parse_family_data(self, fmsData):
        res = []
        for fmData in fmsData.split(';'):
            cs = fmData.split(':')
            if len(cs) != 3:
                raise ValueError("Wrong family data format {}".format(fmData))
            res.append(cs)
        return res

    def load_parse_family_data(self, tmfh, family_data):
        if family_data != 'TOOMANY':
            pfd = self.parse_family_data(family_data)
        else:
            fline = tmfh.readline()
            _ch, _pos, _var, families_data = fline.strip().split('\t')
            pfd = self.parse_family_data(families_data)

        return pfd

    def create_family_variant(self, vs, family_data):
        v = copy.copy(vs)
        v.atts = {kk: vv for kk, vv in vs.atts.items()}
        fid, bs, counts = family_data
        v.atts['familyId'] = fid
        v.atts['bestState'] = bs
        v.atts['counts'] = counts

        return v

    def create_family_variants_dict(self, tmfh, vals, variant):
        family_data = vals['familyData']
        pfd = self.load_parse_family_data(tmfh, family_data)
        res = []
        for fid, bs, c in pfd:
            vs = self.create_family_variant(variant, (fid, bs, c))
            fres = {
                'family_id': vs.familyId,
                'best': vs.bestStStr,
                'counts': vs.countsStr,
            }
            self.build_inchild(fres, vs)
            self.build_inparent(fres, vs)
            res.append(fres)
        return res

    def build_inchild(self, res, vs):
        in_child = vs.inChS
        if 'prb' in in_child:
            res['in_prb'] = 1
            res['in_prb_gender'] = in_child[3]
        if 'sib' in in_child:
            res['in_sib'] = 1
            gender = None
            if in_child.startswith('sib'):
                gender = in_child[3]
            else:
                gender = in_child[7]
            assert gender is not None
            res['in_sib_gender'] = gender
        return res

    def build_inparent(self, res, vs):
        from_parent = vs.fromParentS
        if 'mom' in from_parent:
            res['in_mom'] = 1
        if 'dad' in from_parent:
            res['in_dad'] = 1

    def handle(self, *args, **options):
        if(len(args) != 1):
            raise CommandError('Exactly one argument expected')

        study_name = args[0]
        print("Working with transmitted study: {}".format(study_name))

        (summary_filename, tm_filename) = self.get_study_filenames(study_name)

        with gzip.open(summary_filename, 'r') as fh, \
                gzip.open(tm_filename, 'r') as tmfh:

            column_names = fh.readline().rstrip().split('\t')
            tmfh.readline()  # skip column names in too may family file

            nrow = 0
            for line in fh:
                data = line.strip("\r\n").split("\t")
                vals = dict(zip(column_names, data))
                variant = self.create_summary_variant(vals)

                evvals = self.create_effect_variant_dict(vals)
                svvals = self.create_summary_variant_dict(nrow, vals, evvals)
                fvvals = self.create_family_variants_dict(tmfh, vals, variant)

                sv = SummaryVariant.objects.create(**svvals)
                sv.save()

                evs = []
                for ev in evvals:
                    gev = GeneEffectVariant(
                        summary_variant=sv, **ev)
                    evs.append(gev)
                GeneEffectVariant.objects.bulk_create(evs)

                fvs = []
                for f in fvvals:
                    fv = FamilyVariant(
                        summary_variant=sv, **f)
                    fvs.append(fv)
                FamilyVariant.objects.bulk_create(fvs)

                nrow += 1
                if nrow % 100 == 0:
                    print("line: {}".format(nrow))
