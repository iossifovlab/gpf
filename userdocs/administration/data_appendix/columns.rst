Columns
=======

Preview columns
---------------

========  ========  ===========
Column    Field     Description
========  ========  ===========
family    familyId  Family	ID
\         study     Study name

variant   location  The	position of	the variant in a 1-­‐based coordinate
                    system of hg19 reference assembly.
\         variant   Description of the variant: sub(R-­‐>A) stands for
                    substitution of the reference allele R to an alternative
                    allele A; ins(seq) stands for insertion of the provided
                    sequence (“seq”), and del(N) stands for deletions of
                    N nucleotides
========  ========  ===========

Download columns
----------------

=================== ===========================================================
Field               Description
=================== ===========================================================
familyId            Family ID

study               Study name

phenotype           Study phenotype

location            The position of the variant in a 1-­‐based coordinate
                    system of hg19 reference assembly.

variant             Description of the variant: sub(R-­‐>A) stands for
                    substitution of the reference allele R to an alternative
                    allele A; ins(seq) stands for insertion of the provided
                    sequence (“seq”), and del(N) stands for deletions of
                    N nucleotides

family genotype     The best state according to the Multinomial Model
                    (Experimental Procedures). The format of the column is
                    "momR dadR autR sibR/momA dadA autA sibA" where
                    (for example) momR stands for the number of copies of the
                    reference allele in the mother’s genotype and autA stands
                    for the number of
                    copies of the alternative allele in the genotype of the
                    affected child.

family structure

from parent         Shows the parental haplotypes giving rise to de novo
                    variants
                    when they could be identified.

in child            Shows the affected status and gender of the child in
                    which the
                    de novo variant was observed. The two children are listed
                    when
                    the de novo variant is shared by both.

count               The observed number of reads supporting the different
                    alleles at a given location. The format is
                    <reference allele counts>/<alternative allele counts>/<other allele counts>
                    and the order of individuals is <mom> <dad> <proband> and
                    <sibling>. For example, "10 12 5 20/1 0 8 0/0 0 0 1"
                    indicates that there were 10 reads supporting the reference
                    allele in the mother, there were 8 reads supporting the
                    alternative in the proband, and there was 1 read with a
                    non-­‐reference allele in the unaffected sibling.

alt alleles

parents called      Count of independent parents tested for this variant

worst effect type   The most severe effect the variant has on genes.

genes               The list of gene affected by the variant and the most
                    severe effect for every gene. The format is
                    <gene 1>:<effect on gene 1>|<gene 2>:<effect on gene 2>|.

all effects

effect details      Details of variant effects on each affected isoform.
                    The format is: <isoform 1 of gene 1>; <isoform 2 or gene 1>|<isoform 1 of gene 2>; <isoform 2 of gene 2>|...
                    The amino acid change and the position of the amino acid
                    within the protein are shown.

=================== ===========================================================
