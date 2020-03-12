#!/usr/bin/env python

import sys
import os
from dae.genome import genome_access
from dae.genome.gene_models import load_gene_models
from dae.variant_annotation.annotator import (
    VariantAnnotator as VariantAnnotation,
)

import argparse
import pysam

from Bio import bgzf


def vcfParser(argv):
    # print 'VCF', argv
    parser = argparse.ArgumentParser(
        description="VCF format annotation",
        usage="annotate_variantVCF.py [<args>] <input VCF> <output VCF>",
    )

    parser.add_argument("files", nargs=2, action="store", default=None)
    # parser.add_argument('outputVCF', nargs=1, action='store', default=None )

    parser.add_argument(
        "-P",
        help="promoter length",
        default=0,
        action="store",
        type=int,
        dest="prom_len",
    )

    parser.add_argument(
        "-T", help="gene models ID <RefSeq, CCDS, knownGene>", action="store"
    )
    parser.add_argument(
        "--Traw", help="outside gene models file path", action="store"
    )
    parser.add_argument(
        "--TrawFormat",
        help="outside gene models format (refseq, ccds, knowngene)",
        action="store",
    )
    parser.add_argument(
        "-G",
        help="genome ID <GATK_ResourceBundle_5777_b37_phiX174, hg19> ",
        action="store",
    )
    parser.add_argument("--Graw", help="outside genome file", action="store")
    parser.add_argument(
        "-I",
        "--gene-mapping",
        help="geneIDs mapping file; use None for no gene name mapping",
        default="default",
        action="store",
    )

    return parser


# argColumnNs = [
# chrCol, posCol, locCol, varCol, refCol, altCol, lengthCol, seqCol, typeCol]
def vrt2Eff(annotator, chrom, pos, ref, alts):
    et, eg, ed = [], [], []

    # pxx, vrt = vcf2cshlFormat( pos, ref, alts )
    # for p,v in zip(pxx,vrt):
    # pm = [chrom, p, None, v, None, None, None, None, None]
    for alt in alts:
        pm = [chrom, pos, None, None, ref, alt, None, None, None]
        effects = annotator.do_annotate_variant(*pm)
        t, g, d = annotator.effect_description(effects)
        # print( effects, desc )
        # TODO: delimiter
        # g = g.replace(':','|')
        d = d.replace(";", "|")
        et.append(t)  # effect type#'|'.join( desc ) )
        eg.append(g)  # effect gene
        ed.append(d)  # effect detail
    # TODO: delimiter
    et = ",".join(et)
    eg = ",".join(eg)
    ed = ",".join(ed)

    return et, eg, ed


def getGenomicInfo(opts):
    if opts.gene_mapping == "None":
        opts.gene_mapping = None

    if opts.G is None and opts.Graw is None:
        assert "DAE_DB_DIR" in os.environ
        from dae import GPFInstance

        gpf = GPFInstance()
        genomes_db = gpf.genomes_db

        GA = genomes_db.get_genome()
        if opts.T is None and opts.Traw is None:
            gmDB = genomes_db.get_gene_models()
        elif opts.Traw is None:
            gmDB = genomes_db.get_gene_models(opts.T)
        else:
            gmDB = load_gene_models(opts.Traw, opts.I, opts.TrawFormat)

    elif opts.Graw is None:
        assert "DAE_DB_DIR" in os.environ
        from dae import GPFInstance

        gpf = GPFInstance()
        genomes_db = gpf.genomes_db

        GA = genomes_db.get_genome(opts.G)
        if opts.T is None and opts.Traw is None:
            gmDB = genomes_db.get_gene_models(genomeId=opts.G)
        elif opts.Traw is None:
            gmDB = genomes_db.get_gene_models(opts.T, genomeId=opts.G)
        else:
            gmDB = load_gene_models(opts.Traw, opts.I, opts.TrawFormat)

    else:
        GA = genome_access.open_ref(opts.Graw)
        if opts.Traw is None:
            print(
                "This genome requires gene models (--Traw option)",
                file=sys.stderr,
            )
            sys.exit(1)
        gmDB = load_gene_models(opts.Traw, opts.I, opts.TrawFormat)

    if "1" in GA.chromosomes and "1" not in gmDB.utr_models.keys():
        gmDB.relabel_chromosomes()

    return GA, gmDB


def openFile(fName, mode="r"):
    """
            mode should be 'r' or 'w'
            and how to read/write depends on type of file
    """
    if fName.endswith(".gz"):
        return bgzf.open(fName, mode + "b")

    return open(fName, mode)


def process(argv=sys.argv[1:]):

    parser = vcfParser(argv)
    args = parser.parse_args(argv)

    if ("DAE_DB_DIR" not in os.environ) and (not args.Graw or not args.Traw):
        print(
            'An env variable, "DAE_DB_DIR", is not defined \n'
            "\tGenome (--Graw) and Genes' Model (--Traw) "
            "should be explicitly defined in options",
            file=sys.stderr,
        )
        sys.exit(0)

    GA, gmDB = getGenomicInfo(args)

    infile, outfile = args.files
    if not os.path.exists(infile):
        sys.stderr.write("The '%s' file is not found!\n" % infile)
        sys.exit(1)

    variantFile = pysam.VariantFile(infile)

    if os.path.exists(outfile):
        sys.stderr.write("The '%s' file exist!\n" % outfile)
        sys.exit(1)

    outFile = openFile(outfile, "w")

    annotator = VariantAnnotation(GA, gmDB, promoter_len=args.prom_len)

    # TODO: COPY, remove after implimentation
    # f.header.info.add( 'ET', '.', 'String', 'effective type' )
    # add header
    # f.header.add_meta( 'Info', 'Hello' ) st "geneEffect",
    # its commands and so on
    # vrt.info['ET'] = 'hello'
    head = variantFile.header  # .copy()
    head.add_meta("annotated", "geneEffects4Variants")
    head.add_meta("annotatedCommand", '"{}"'.format(" ".join(sys.argv)))

    head.info.add("eT", ".", "String", "effected type")
    head.info.add("eG", ".", "String", "effected gene")
    head.info.add("eD", ".", "String", "effect Details")

    print(str(head), file=outFile, end="")

    k = 0
    for vrt in variantFile:
        k += 1
        if k % 1000 == 0:
            sys.stderr.write(str(k) + " lines processed\n")

        et, eg, ed = vrt2Eff(annotator, vrt.chrom, vrt.pos, vrt.ref, vrt.alts)

        vrt.info["eT"] = et
        vrt.info["eG"] = eg
        vrt.info["eD"] = ed
        print(str(vrt), file=outFile, end="")

    outFile.close()


if __name__ == "__main__":
    process()
