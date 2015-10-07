'''
Created on Aug 28, 2015

@author: lubo
'''
from django.core.management.base import BaseCommand, CommandError
from DAE import vDB
import gzip
import copy
from VariantsDB import Variant


FAMILY_VARIANTS_CREATE_TABLE = '''
DROP TABLE IF EXISTS `transmitted_familyvariant`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `transmitted_familyvariant` (
  `family_id` varchar(16) NOT NULL,
  `best` varchar(16) NOT NULL,
  `counts` varchar(64) NOT NULL,
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
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;
'''

FAMILY_VARIANTS_BEGIN_DUMPING_DATA = '''
--
-- Dumping data for table `transmitted_familyvariant`
--

LOCK TABLES `transmitted_familyvariant` WRITE;
/*!40000 ALTER TABLE `transmitted_familyvariant` DISABLE KEYS */;
'''

FAMILY_VARIANTS_END_DUMPING_DATA = '''
/*!40000 ALTER TABLE `transmitted_familyvariant` ENABLE KEYS */;
UNLOCK TABLES;

'''

FAMILY_VARIANTS_INSERT_BEGIN = \
    '''INSERT INTO `transmitted_familyvariant` VALUES '''

FAMILY_VARIANTS_VALUES = \
    '''( '%(family_id)s', '%(best)s', '%(counts)s',''' \
    ''' %(in_mom)d, %(in_dad)d, %(in_prb)d, '%(in_prb_gender)s',''' \
    ''' %(in_sib)d,''' \
    ''' '%(in_sib_gender)s', %(summary_variant_id)d)'''


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

        return FAMILY_VARIANTS_VALUES % res

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

    def handle(self, *args, **options):
        if(len(args) != 1):
            raise CommandError('Exactly one argument expected')

        study_name = args[0]
        print("Working with transmitted study: {}".format(study_name))

        (summary_filename, tm_filename) = self.get_study_filenames(study_name)

        with gzip.open(summary_filename, 'r') as fh, \
                gzip.open(tm_filename, 'r') as tmfh, \
                open('family_variants_innod.sql', 'w') as outfile:

            column_names = fh.readline().rstrip().split('\t')
            tmfh.readline()  # skip column names in too may family file

            outfile.write(FAMILY_VARIANTS_CREATE_TABLE)
            outfile.write('\n')
            outfile.write(FAMILY_VARIANTS_BEGIN_DUMPING_DATA)
            outfile.write('\n')

            vrow = 1
            for line in fh:
                data = line.strip("\r\n").split("\t")
                vals = dict(zip(column_names, data))

                variant = self.create_summary_variant(vals)

                fv_values = self.create_family_variants_values(tmfh,
                                                               vals,
                                                               vrow,
                                                               variant)

                fv_insert = '%s %s;' % (FAMILY_VARIANTS_INSERT_BEGIN,
                                        ','.join(fv_values))

                outfile.write(fv_insert)
                outfile.write('\n')

                if vrow % 1000 == 0:
                    print("line: {}".format(vrow))
                vrow += 1

            outfile.write(FAMILY_VARIANTS_END_DUMPING_DATA)
            outfile.write('\n')
