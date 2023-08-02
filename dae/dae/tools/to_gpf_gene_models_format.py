#!/usr/bin/env python
import optparse

from dae.genomic_resources.gene_models import build_gene_models_from_file

DESC = """Program to annotate variants (substitutions & indels & cnvs)"""


parser = optparse.OptionParser(
    version="%prog version 1.0 11/October/2013", description=DESC
)
parser.add_option(
    "--gm_format",
    help="gene models format (refseq, ccds or knowngene)",
    type="string",
    action="store",
)
parser.add_option(
    "--gm_names",
    help="gene names mapping file [type None for no mapping]",
    default=None,
    type="string",
    action="store",
)
parser.add_option(
    "--chr_names",
    help="chromosome names mapping file",
    type="string",
    action="store",
)

(opts, args) = parser.parse_args()


if len(args) < 2:
    print(
        "The script requires 2 mandatory arguments:\n\t"
        "1. gene models input file\n\t"
        "2. output file [no extension]"
    )
    # sys.exit(-1)
    args = ["gencode.v43.annotation.gtf.gz", "cc"]

from_filename = args[0]
to_filename = args[1]


gene_models = build_gene_models_from_file(
    from_filename, file_format=opts.gm_format,
    gene_mapping_file_name=opts.gm_names
)
gene_models.load()
if opts.chr_names is not None:
    gene_models.relabel_chromosomes(opts.chr_names)

# else:
#     gene_models.relabel_chromosomes()
# save_dicts(gene_models, outputFile = to_filename)
gene_models.save(to_filename)
