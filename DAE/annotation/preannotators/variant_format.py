import GenomeAccess
import common.config
from annotation.tools.utilities import *
from utils.vcf import cshl_format
from utils.dae import dae2vcf_variant

def get_arguments():
    return {
        '-c': {
            'help': 'chromosome column number/name'
        },
        '-p': {
            'help': 'position column number/name'
        },
        '-x': {
            'help': 'location (chr:position) column number/name'
        },
        '-v': {
            'help': 'variant (CSHL format) column number/name'
        },
        '-r': {
            'help': 'reference column number/name'
        },
        '-a': {
            'help': 'alternative column number/name'
        },
        '--vcf': {
            'help': 'if the variant position is in VCF semantics',
            'default': False,
            'action': 'store_true'
        },
        '--Graw': {
            'help': 'genome file location'
        }
    }

class VariantFormatPreannotator(AnnotatorBase):
    """
    `VariantFormatPreannotator` is a `Preannotator` for creating
    columns who are used for annotation of data.

    Generated virtual columns are:

    * `CSHL:location` - location in CSHL format

    * `CSHL:chr` - chromosome in CSHL format

    * `CSHL:position` - position in CSHL format

    * `CSHL:variant` - variant in CSHL format

    * `VCF:chr` - chromosome in VCF format

    * `VCF:position` - position in VCF format

    * `VCF:ref` - reference in VCF format

    * `VCF:alt` - alternative in VCF format
    """ 
    def __init__(self, opts, header=None):
        self._new_columns = [
            'CSHL:location', 'CSHL:chr', 'CSHL:position', 'CSHL:variant',
            'VCF:chr', 'VCF:position', 'VCF:ref', 'VCF:alt'
        ]
        if opts.vcf:
            if opts.c is None:
                opts.c = 'CHROM'
            if opts.p is None:
                opts.p = 'POS'
            if opts.r is None:
                opts.r = 'REF'
            if opts.a is None:
                opts.a = 'ALT'
            self.arg_columns = [assign_values(col, header)
                                for col in [opts.c, opts.p, opts.r, opts.a]]
            self._generate_columns = self._from_vcf
        else:
            if opts.x is None and opts.c is None:
                opts.x = 'location'
            if opts.v is None:
                opts.v = 'variant'
            self.arg_columns = [assign_values(col, header)
                                for col in [opts.c, opts.p, opts.x, opts.v]]
            self._generate_columns = self._from_dae
            if opts.Graw is None:
                from DAE import genomesDB
                self.GA = genomesDB.get_genome()
            else:
                self.GA = GenomeAccess.openRef(opts.Graw)

    @property
    def new_columns(self):
        return self._new_columns

    def _from_dae(self, chromosome=None, position=None, location=None,
            variant=None):
        if location is not None:
            chromosome, position = location.split(':')
        else:
            location = '{}:{}'.format(chromosome, position)
        vcf_position, ref, alt = dae2vcf_variant(chromosome, int(position),
            variant, self.GA)
        return {
            'CSHL:location': location,
            'CSHL:chr': chromosome,
            'CSHL:position': str(position),
            'CSHL:variant': variant,
            'VCF:chr': chromosome,
            'VCF:position': str(vcf_position),
            'VCF:ref': ref,
            'VCF:alt': alt
        }

    def _from_vcf(self, chromosome, position, reference, alternative):
        cshl_position, variant, _ = cshl_format(int(position), reference,
            alternative)
        return {
            'CSHL:location': '{}:{}'.format(chromosome, cshl_position),
            'CSHL:chr': chromosome,
            'CSHL:position': str(cshl_position),
            'CSHL:variant': variant,
            'VCF:chr': chromosome,
            'VCF:position': str(position),
            'VCF:ref': reference,
            'VCF:alt': alternative
        }

    def line_annotations(self, line, new_columns):
        if len(new_columns) == 0:
            return []
        params = [line[i-1] if i!=None else None for i in self.arg_columns]
        values = self._generate_columns(*params)
        return [values[col] for col in new_columns]
