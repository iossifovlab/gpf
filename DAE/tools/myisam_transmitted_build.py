#!/usr/bin/env python
# encoding: utf-8
'''
myisam_transmitted_build.py -- prepares MySQL statements for a study.

myisam_transmitted_build.py is a tool for building SQL files for representing
transmitted studies into MySQL MYISAM tables.

@author:     lubo

@contact:    lubomir.chorbadjiev@gmail.com
'''
from __future__ import print_function
from __future__ import unicode_literals

from builtins import str
from builtins import zip
from builtins import object
import sys
import os

from argparse import ArgumentParser
from argparse import RawDescriptionHelpFormatter

from DAE import vDB
from Variant import Variant, parseGeneEffect
import gzip
import copy
from VariantsDB import Study

__all__ = []
__version__ = 0.1
__date__ = '2015-10-15'
__updated__ = '2015-10-15'

DEBUG = 0
TESTRUN = 0
PROFILE = 0


class CLIError(Exception):
    '''Generic exception to raise and log different fatal errors.'''

    def __init__(self, msg):
        super(CLIError).__init__(type(self))
        self.msg = "E: %s" % msg

    def __str__(self):
        return self.msg

    def __unicode__(self):
        return self.msg


class VariantsBase(object):

    def create_summary_variant_dict(
            self, nrow, vals, evvals, score_names=None):
        res = {
            'id': nrow,
            'ln': nrow,
            'chrome': vals['chr'],
            'position': int(vals['position']),
            'variant': vals['variant'],
            'variant_type': vals['variant'][:3],
            'effect_type': evvals[0]['effect_type'] if evvals else 'NULL',
            'effect_gene': evvals[0]['symbol'] if evvals else 'NULL',
            'effect_gene_all': vals['effectGene'],
            'effect_count': len(evvals),
            'effect_details': vals['effectDetails'],
            'n_par_called': int(vals['all.nParCalled']),
            'n_alt_alls': int(vals['all.nAltAlls']),
            'alt_freq': float(vals['all.altFreq']),
            'prcnt_par_called': float(vals['all.prcntParCalled']),
            'hw': float(vals['HW']),
            'ssc_freq': self.safe_float(vals.get('SSC-freq', None)),
            'evs_freq': self.safe_float(vals.get('EVS-freq', None)),
            'e65_freq': self.safe_float(vals.get('E65-freq', None)),
        }
        if score_names:
            for sn in score_names:
                res[sn] = self.safe_float(vals[sn])

        return res

    @staticmethod
    def safe_float(s):
        if s is None:
            return 'NULL'
        if s.strip() == '':
            return 'NULL'
        if s.strip() == '.':
            return 'NULL'
        if s.strip() == '-':
            return 'NULL'
        return s

    @staticmethod
    def get_study_filenames(study_name):
        study = vDB.get_study(study_name)

        summary_filename = study.vdb._config.get(
            study._configSection,
            'transmittedVariants.indexFile') + ".txt.bgz"
        tm_filename = study.vdb._config.get(
            study._configSection,
            'transmittedVariants.indexFile') + "-TOOMANY.txt.bgz"
        return (study, summary_filename, tm_filename)

    @staticmethod
    def build_study_filenames(study_name, args):
        assert os.path.exists(args.familiesfile)
        assert os.path.exists(args.transmittedfile)
        assert os.path.exists(args.toomanyfile)

        _base, ext = os.path.splitext(args.familiesfile)
        if ext == '.pckl':
            families, _ = Study._load_family_data_from_pickle(
                args.familiesfile)
        else:
            families, _ = Study._load_family_data_from_simple(
                args.familiesfile)

        class StudyMock(object):
            def __init__(self, study_name, families):
                self.name = study_name
                self.families = families

        study = StudyMock(study_name, families)
        return (study, args.transmittedfile, args.toomanyfile)

#         else:
#             study = vDB.get_study(study_name)
#             summary_filename = study.vdb._config.get(
#                 study._configSection,
#                 'transmittedVariants.indexFile') + ".txt.bgz"
#             tm_filename = study.vdb._config.get(
#                 study._configSection,
#                 'transmittedVariants.indexFile') + "-TOOMANY.txt.bgz"
#             return (study, summary_filename, tm_filename)

    def create_effect_variant_dict(self, vals, vrow, erow):
        gene_effects = parseGeneEffect(vals['effectGene'])
        variant_type = vals['variant'][0:3]

        if len(gene_effects) == 0 and vals['effectGene'] == 'intergenic':
            erow += 1
            return erow, [{
                'id': erow,
                'symbol': 'NULL',
                'effect_type': 'intergenic',
                'variant_type': variant_type,
                'n_par_called': int(vals['all.nParCalled']),
                'n_alt_alls': int(vals['all.nAltAlls']),
                'alt_freq': float(vals['all.altFreq']),
                'summary_variant_id': vrow,
            }]

        res = []
        for ge in gene_effects:
            erow += 1
            eres = {
                'id': erow,
                'symbol': '"%s"' % ge['sym'],
                'effect_type': ge['eff'],
                'variant_type': variant_type,
                'n_par_called': int(vals['all.nParCalled']),
                'n_alt_alls': int(vals['all.nAltAlls']),
                'alt_freq': float(vals['all.altFreq']),
                'summary_variant_id': vrow,
            }
            res.append(eres)
        return erow, res


class SummaryVariants(VariantsBase):
    CREATE_TABLE = '''
--
-- Table structure for table `transmitted_summaryvariant`
--

DROP TABLE IF EXISTS `transmitted_summaryvariant`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `transmitted_summaryvariant` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `ln` int(11) NOT NULL,
  `chrome` varchar(3) NOT NULL,
  `position` int(11) NOT NULL,
  `variant` varchar(90) NOT NULL,
  `variant_type` varchar(4) NOT NULL,
  `effect_type` varchar(32) DEFAULT NULL,
  `effect_gene` varchar(32) DEFAULT NULL,
  `effect_gene_all` varchar(1024) DEFAULT NULL,
  `effect_count` int(11) NOT NULL,
  `effect_details` varchar(1024) DEFAULT NULL,
  `n_par_called` int(11) NOT NULL,
  `n_alt_alls` int(11) NOT NULL,
  `alt_freq` double NOT NULL,
  `prcnt_par_called` double NOT NULL,
  `hw` double NOT NULL,
  {}
  `ssc_freq` double DEFAULT NULL,
  `evs_freq` double DEFAULT NULL,
  `e65_freq` double DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `transmitted_summaryvariant_f8e19f44` (`ln`),
  KEY `transmitted_summaryvariant_554838a8` (`chrome`),
  KEY `transmitted_summaryvariant_91ca6089` (`effect_type`),
  KEY `transmitted_summaryvariant_7f96c587` (`effect_gene`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;
'''

    BEGIN_DUMPING_DATA = '''
--
-- Dumping data for table `transmitted_summaryvariant`
--

LOCK TABLES `transmitted_summaryvariant` WRITE;
/*!40000 ALTER TABLE `transmitted_summaryvariant` DISABLE KEYS */;
'''

    END_DUMPING_DATA = '''
/*!40000 ALTER TABLE `transmitted_summaryvariant` ENABLE KEYS */;
UNLOCK TABLES;
'''

    INSERT_BEGIN = \
        '''INSERT INTO `transmitted_summaryvariant` VALUES %s ;'''

    VALUES = \
        '''( %(id)d, %(ln)d, "%(chrome)s", %(position)d, ''' \
        ''' "%(variant)s", "%(variant_type)s", ''' \
        ''' "%(effect_type)s", %(effect_gene)s, "%(effect_gene_all)s", ''' \
        ''' %(effect_count)d, "%(effect_details)s", ''' \
        ''' %(n_par_called)d, %(n_alt_alls)d, %(alt_freq)f, ''' \
        ''' %(prcnt_par_called)f, %(hw)f, ''' \
        ''' {} ''' \
        ''' %(ssc_freq)s, %(evs_freq)s, %(e65_freq)s )\n'''

    def create_table_statement(self, score_names=None):
        if not score_names:
            return self.CREATE_TABLE.format("")
        scores = [
            "`{}`  double DEFAULT NULL".format(name) for name in score_names
        ]
        create = ",\n".join(scores) + ",\n"
        return self.CREATE_TABLE.format(create)

    def values_statement(self, score_names=None):
        if not score_names:
            return self.VALUES.format("")
        statements = [" %({})s, ".format(name) for name in score_names]
        return self.VALUES.format("".join(statements))

    def handle(self, study_name, summary_filename, outdir, score_names=None):

        print("Working with transmitted study: {}".format(study_name))
        print("Working with summary filename: {}".format(summary_filename))
        print("Working with score names: {}".format(score_names))
        outfilename = os.path.join(
            outdir,
            '{}_sql_summary_variants_myisam.sql.gz'.format(study_name)
        )

        with gzip.open(summary_filename, 'r') as fh, \
                gzip.open(outfilename, 'w') as outfile:

            column_names = fh.readline().rstrip().split('\t')
            column_names = [cn.strip("#") for cn in column_names]

            if score_names:
                for sc in score_names:
                    assert sc in column_names, sc

            # assert score_names is None or all(
            #     [sc in column_names for sc in score_names])
            create_table_sql = self.create_table_statement(score_names)
            values_sql = self.values_statement(score_names)

            outfile.write(create_table_sql)
            outfile.write('\n')
            outfile.write(self.BEGIN_DUMPING_DATA)
            outfile.write('\n')

            nrow = 1
            erow = 0
            ins_line = []
            for line in fh:
                try:
                    if line[0] == '#':
                        print('skipping comment: {}'.format(line.strip()))
                        continue
                    data = line.strip("\r\n").split("\t")
                    vals = dict(list(zip(column_names, data)))
                    erow, evvals = \
                        self.create_effect_variant_dict(vals, nrow, erow)
                    svvals = self.create_summary_variant_dict(
                        nrow, vals, evvals, score_names=score_names)
                    ins_values = values_sql % svvals
                    ins_line.append(ins_values)
                    nrow += 1
                    if nrow % 100 == 0:
                        outfile.write(self.INSERT_BEGIN %
                                      ', '.join(ins_line))
                        outfile.write('\n')
                        ins_line = []
                        sys.stderr.write('.')
                except Exception as ex:
                    import traceback
                    print(
                        "exception thrown during processing row {};"
                        " line: |{}|; data: {}; vals: {}"
                        .format(nrow, line, data, vals))
                    traceback.print_exc()
                    raise ex
            if ins_line:
                outfile.write(self.INSERT_BEGIN %
                              ', '.join(ins_line))
                outfile.write('\n')

            outfile.write(self.END_DUMPING_DATA)
            outfile.write('\n')
            sys.stderr.write('\n')


class GeneEffectVariants(VariantsBase):
    CREATE_TABLE = '''
--
-- Table structure for table `transmitted_geneeffectvariant`
--

DROP TABLE IF EXISTS `transmitted_geneeffectvariant`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `transmitted_geneeffectvariant` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `symbol` varchar(32) DEFAULT NULL,
  `effect_type` varchar(32) NOT NULL,
  `variant_type` varchar(4) NOT NULL,
  `n_par_called` int(11) NOT NULL,
  `n_alt_alls` int(11) NOT NULL,
  `alt_freq` double NOT NULL,
  `summary_variant_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `transmitted_geneeffectvariant_97bff268` (`symbol`),
  KEY `transmitted_geneeffectvariant_91ca6089` (`effect_type`),
  KEY `transmitted_geneeffectvariant_fd9ab97c` (`summary_variant_id`),
  CONSTRAINT `d3a6ab47e8f9acff1fd095bac97aa175`
  FOREIGN KEY (`summary_variant_id`)
  REFERENCES `transmitted_summaryvariant` (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;
'''

    BEGIN_DUMPING_DATA = '''
--
-- Dumping data for table `transmitted_geneeffectvariant`
--

LOCK TABLES `transmitted_geneeffectvariant` WRITE;
/*!40000 ALTER TABLE `transmitted_geneeffectvariant` DISABLE KEYS */;
'''

    END_DUMPING_DATA = '''
/*!40000 ALTER TABLE `transmitted_geneeffectvariant` ENABLE KEYS */;
UNLOCK TABLES;


'''

    INSERT_BEGIN = \
        '''INSERT INTO `transmitted_geneeffectvariant` VALUES %s ;'''

    VALUES = \
        '''( %(id)d, %(symbol)s, "%(effect_type)s", "%(variant_type)s", ''' \
        '''  %(n_par_called)d, %(n_alt_alls)d, %(alt_freq)f, ''' \
        '''  %(summary_variant_id)d )'''

    def handle(self, study_name, summary_filename, outdir):

        print("Working with transmitted study: {}".format(study_name))
        print("Working with summary filename: {}".format(summary_filename))
        outfilename = os.path.join(
            outdir,
            '{}_sql_gene_effect_variants_myisam.sql.gz'.format(study_name)
        )
        print("Storing result into: {}".format(outfilename))

        with gzip.open(summary_filename, 'r') as fh, \
                gzip.open(outfilename, 'w') as outfile:

            column_names = fh.readline().rstrip().split('\t')

            outfile.write(self.CREATE_TABLE)
            outfile.write('\n')
            outfile.write(self.BEGIN_DUMPING_DATA)
            outfile.write('\n')

            vrow = 1
            erow = 1
            ins_line = []
            for line in fh:
                try:
                    if line[0] == '#':
                        print('skipping comment: {}'.format(line.strip()))
                        continue
                    data = line.strip("\r\n").split("\t")
                    vals = dict(list(zip(column_names, data)))
                    erow, evvals = \
                        self.create_effect_variant_dict(vals, vrow, erow)
                    ins_values = [self.VALUES % ev
                                  for ev in evvals]
                    ins_line.extend(ins_values)
                    vrow += 1
                    if vrow % 100 == 0:
                        outfile.write(self.INSERT_BEGIN %
                                      ', '.join(ins_line))
                        outfile.write('\n')
                        ins_line = []
                        sys.stderr.write('.')
                except Exception as ex:
                    import traceback
                    print("exception thrown during processing line: |{}|"
                          .format(line))
                    traceback.print_exc()
                    raise ex

            if ins_line:
                outfile.write(self.INSERT_BEGIN %
                              ', '.join(ins_line))
                outfile.write('\n')

            outfile.write(self.END_DUMPING_DATA)
            outfile.write('\n')
            sys.stderr.write('\n')


class FamilyVariants(VariantsBase):
    CREATE_TABLE = '''
DROP TABLE IF EXISTS `transmitted_familyvariant`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `transmitted_familyvariant` (
  `family_id` varchar(32) NOT NULL,
  `best` varchar(32) NOT NULL,
  `counts` varchar(128) NOT NULL,
  `in_mom` tinyint(1) NOT NULL,
  `in_dad` tinyint(1) NOT NULL,
  `in_prb` tinyint(1) NOT NULL,
  `in_prb_gender` varchar(1) DEFAULT NULL,
  `in_sib` tinyint(1) NOT NULL,
  `in_sib_gender` varchar(1) DEFAULT NULL,
  `summary_variant_id` int(11) NOT NULL,
  PRIMARY KEY (`family_id`, `summary_variant_id`),
  KEY `transmitted_familyvariant_0caa70f7` (`family_id`),
  KEY `transmitted_familyvariant_fd9ab97c` (`summary_variant_id`),
  CONSTRAINT `D1b9d36c68906398c84f8ef06314d61c`
  FOREIGN KEY (`summary_variant_id`)
  REFERENCES `transmitted_summaryvariant` (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;
'''

    BEGIN_DUMPING_DATA = '''
--
-- Dumping data for table `transmitted_familyvariant`
--

LOCK TABLES `transmitted_familyvariant` WRITE;
/*!40000 ALTER TABLE `transmitted_familyvariant` DISABLE KEYS */;
'''

    END_DUMPING_DATA = '''
/*!40000 ALTER TABLE `transmitted_familyvariant` ENABLE KEYS */;
UNLOCK TABLES;
'''

    INSERT_BEGIN = \
        '''INSERT INTO `transmitted_familyvariant` VALUES '''

    VALUES = \
        '''( '%(family_id)s', '%(best)s', '%(counts)s',''' \
        ''' %(in_mom)d, %(in_dad)d, %(in_prb)d, '%(in_prb_gender)s',''' \
        ''' %(in_sib)d,''' \
        ''' '%(in_sib_gender)s', %(summary_variant_id)d)'''

    def __init__(self, study):
        self.study = study

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
        v.atts = {kk: vv for kk, vv in list(vs.atts.items())}
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

    def create_family_variant_value(self, fid, bs, c, vrow, variant):
        fvar = self.create_family_variant(variant, (fid, bs, c))
        res = {'summary_variant_id': vrow,
               'family_id': fid,
               'best': bs,
               'counts': c,
               'in_mom': 0,
               'in_dad': 0,
               'in_prb': 0,
               'in_sib': 0,
               'in_prb_gender': 'M',
               'in_sib_gender': 'M'}
        self.build_inchild(res, fvar)
        self.build_inparent(res, fvar)
        return self.VALUES % res

    def create_family_variants_values(self, tmfh, vals, vrow, variant):
        family_data = vals['familyData']

        pfd = self.load_parse_family_data(tmfh, family_data)
        res = []
        for fid, bs, c in pfd:
            fin = self.create_family_variant_value(fid, bs, c, vrow, variant)
            res.append(fin)
        return res

    def create_summary_variant(self, vals):
        vals["location"] = vals["chr"] + ":" + vals["position"]
        v = Variant(vals)
        v.study = self.study
        if int(vals['all.nAltAlls']) == 1:
            v.popType = 'ultraRare'
        else:
            v.popType = 'common'
        return v

    def handle(self, study_name, summary_filename, tm_filename, outdir):

        print("Working with transmitted study: {}".format(study_name))
        print("Working with summary filename: {}".format(summary_filename))
        outfilename = os.path.join(
            outdir,
            '{}_sql_family_variants_myisam.sql.gz'.format(study_name)
        )
        print("Storing result into: {}".format(outfilename))
        print("Working with transmitted study: {}".format(study_name))

        with gzip.open(summary_filename, 'r') as fh, \
                gzip.open(tm_filename, 'r') as tmfh, \
                gzip.open(outfilename, 'w') as outfile:

            column_names = fh.readline().rstrip().split('\t')
            column_names = [cn.strip("#") for cn in column_names]

            tmfh.readline()  # skip column names in too may family file

            outfile.write(self.CREATE_TABLE)
            outfile.write('\n')
            outfile.write(self.BEGIN_DUMPING_DATA)
            outfile.write('\n')

            vrow = 1
            for line in fh:
                try:
                    if line[0] == '#':
                        print('skipping comment: {}'.format(line.strip()))
                        continue
                    data = line.strip("\r\n").split("\t")
                    vals = dict(list(zip(column_names, data)))

                    variant = self.create_summary_variant(vals)

                    fv_values = self.create_family_variants_values(
                        tmfh,
                        vals,
                        vrow,
                        variant)

                    fv_insert = '%s %s;' % (self.INSERT_BEGIN,
                                            ','.join(fv_values))

                    outfile.write(fv_insert)
                    outfile.write('\n')

                    if vrow % 100 == 0:
                        sys.stderr.write('.')
                    vrow += 1
                except Exception as ex:
                    import traceback
                    print("exception thrown during processing line: |{}|"
                          .format(line))
                    traceback.print_exc()
                    raise ex

            sys.stderr.write('\n')
            outfile.write(self.END_DUMPING_DATA)
            outfile.write('\n')


def main(argv=None):  # IGNORE:C0111
    '''Command line options.'''

    if argv is None:
        argv = sys.argv
    else:
        sys.argv.extend(argv)

    program_name = os.path.basename(sys.argv[0])
    program_version = "v%s" % __version__
    program_build_date = str(__updated__)
    program_version_message = '%%(prog)s %s (%s)' % \
        (program_version, program_build_date)
    program_shortdesc = __import__('__main__').__doc__.split("\n")[1]
    program_desc = '''%s
%s
USAGE
''' % (program_shortdesc, str(__date__))

    try:
        # Setup argument parser
        parser = ArgumentParser(description=program_desc,
                                formatter_class=RawDescriptionHelpFormatter)
        parser.add_argument(
            "-s", "--summary",
            dest="summary",
            action="store_true",
            help="builds summary vartiants table [default: %(default)s]")
        parser.add_argument(
            "-e", "--geneeffect",
            dest="gene_effect",
            action="store_true",
            help="builds gene effect variants table [default: %(default)s]")
        parser.add_argument(
            "-f", "--family",
            dest="family",
            action="store_true",
            help="builds family variants table [default: %(default)s]")

        parser.add_argument(
            "-a", "--all",
            dest="all",
            action="store_true",
            help="builds all variants table [default: %(default)s]")

        parser.add_argument(
            "-o", "--outdir",
            default='.',
            dest="outdir",
            help="output directory where to store SQL files."
            "[default: %(default)s]")
        parser.add_argument(
            '-V', '--version',
            action='version', version=program_version_message)

        parser.add_argument(
            '-S', '--studyname',
            dest="study_name",
            help="study name to process "
            "[default: %(default)s]", metavar="study_name")

        parser.add_argument(
            '-F', '--familiesfile',
            dest="familiesfile",
            help="study families filename",
            metavar='familes')

        parser.add_argument(
            '-T', '--transmittedfile',
            dest='transmittedfile',
            help='transmitted variants base file name')

        parser.add_argument(
            '-M', '--toomanyfile',
            dest='toomanyfile',
            help='transmitted variants family variants file name')

        parser.add_argument(
            '-G', '--genomic_scores',
            dest='genomic_scores',
            help='list of genomic scores to transfer into MySQL tables')
        parser.add_argument(
            '--genomic_scores_filename',
            dest='genomic_scores_filename',
            help='file with list of genomic scores to transfer into MySQL tables')

        args = parser.parse_args()

        study_name = args.study_name
        outdir = args.outdir

        summary = args.summary
        gene_effect = args.gene_effect
        family = args.family

        genomic_scores = None
        if args.genomic_scores:
            genomic_scores = args.genomic_scores.split(",")
        if genomic_scores is None and args.genomic_scores_filename:
            with open(args.genomic_scores_filename, "r") as infile:
                lines = infile.readlines()
                lines = [ln.strip() for ln in lines]
                genomic_scores = [ln for ln in lines if ln]

        if args.all:
            summary = True
            gene_effect = True
            family = True

        study, summary_filename, tm_filename = \
            VariantsBase.build_study_filenames(study_name, args)

        print((study.name, summary_filename, tm_filename))
        if summary:
            summary_variants = SummaryVariants()
            summary_variants.handle(
                study_name, summary_filename, outdir,
                score_names=genomic_scores)
        if gene_effect:
            gene_effect_variants = GeneEffectVariants()
            gene_effect_variants.handle(study_name, summary_filename, outdir)

        if family:
            family_variants = FamilyVariants(study)
            family_variants.handle(study_name, summary_filename,
                                   tm_filename, outdir)
        return 0
    except KeyboardInterrupt:
        # handle keyboard interrupt
        return 0
    except Exception as e:
        import traceback
        traceback.print_exc()

        if DEBUG or TESTRUN:
            raise(e)
        indent = len(program_name) * " "
        sys.stderr.write(program_name + ": " + repr(e) + "\n")
        sys.stderr.write(indent + "  for help use --help")
        return 2


if __name__ == "__main__":
    sys.exit(main())
