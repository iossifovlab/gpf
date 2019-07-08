Genotype Browser Section
========================


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



Gene Weights
----------------


LGD rank
........

RVIS rank
.........

pLI rank
........


Genomic Scores
----------------


====================================    ========================================================================================================
Field                                   Description
====================================    ========================================================================================================
phyloP100                                Link: http://hgdownload.cse.ucsc.edu/goldenpath/hg19/phyloP100way/.
                                         Conservation scoring by phyloP (phylogenetic p-values) from the
                                         PHAST package (http://compgen.bscb.cornell.edu/phast/) for multiple
                                         alignments of 99 vertebrate genomes to the human genome.

                                         .. image:: imgs/genomic_scores/phyloP100.png
                                             :scale: 30
                                             :alt: phyloP100
                                             :align: center


phyloP46_vertebrates                     Link: http://hgdownload.cse.ucsc.edu/goldenpath/hg19/phyloP46way/.
                                         Conservation scoring by phyloP (phylogenetic p-values) from the
                                         PHAST package (http://compgen.bscb.cornell.edu/phast/) for multiple
                                         alignments of 45 vertebrate genomes to the human genome, plus alternate
                                         sets of scores for the primate species and the placental mammal species
                                         in the alignments.

                                         .. image:: imgs/genomic_scores/phyloP46_vertebrates.png
                                             :scale: 30
                                             :alt: phyloP46_vertebrates
                                             :align: center

phyloP46_placentals                      Alternate set of phyloP46_vertebrates scores for the placental mammal
                                         subset of species in the alignments.

                                         .. image:: imgs/genomic_scores/phyloP46_placentals.png
                                             :scale: 30
                                             :alt: phyloP46_placentals
                                             :align: center

phyloP46_primates                        Alternate set of phyloP46_vertebrates scores for the primates subset species
                                         in the alignments.

                                         .. image:: imgs/genomic_scores/phyloP46_primates.png
                                             :scale: 30
                                             :alt: phyloP46_primates
                                             :align: center

phastCons100                             Link: http://hgdownload.cse.ucsc.edu/goldenpath/hg19/phastCons100way/.
                                         Compressed phastCons scores for multiple alignments of 99 vertebrate
                                         genomes to the human genome. PhastCons is a program for identifying
                                         evolutionarily conserved elements in a multiple alignment, given a
                                         phylogenetic tree.

                                         .. image:: imgs/genomic_scores/phastCons100.png
                                             :scale: 30
                                             :alt: phastCons100
                                             :align: center

phastCons46_vertebrates                  Link: http://hgdownload.cse.ucsc.edu/goldenpath/hg19/phastCons46way/.
                                         Compressed phastCons scores for multiple alignments of 45 vertebrate genomes
                                         to the human genome, plus an alternate set of scores for the primates subset
                                         of species in the alignments, and an alternate set of scores for the placental
                                         mammal subset of species in the alignments. PhastCons is a program for
                                         identifying evolutionarily conserved elements in a multiple alignment,
                                         given a phylogenetic tree.

                                         .. image:: imgs/genomic_scores/phastCons46_vertebrates.png
                                             :scale: 30
                                             :alt: phastCons46_vertebrates
                                             :align: center

phastCons46_placentals                   Alternate set of phastCons46_vertebrates scores for the placental mammal subset
                                         of species in the alignments.

                                         .. image:: imgs/genomic_scores/phastCons46_placentals.png
                                             :scale: 30
                                             :alt: phastCons46_placentals
                                             :align: center

phastCons46_primates                     Alternate set of phastCons46_vertebrates scores for the primates subset of
                                         species in the alignments.

                                         .. image:: imgs/genomic_scores/phastCons46_primates.png
                                             :scale: 30
                                             :alt: phastCons46_primates
                                             :align: center

CADD_raw                                 Link: https://cadd.gs.washington.edu/download ; Higher values of raw
                                         scores have relative meaning that a variant is more likely to be simulated
                                         (or "not observed") and therefore more likely to have deleterious effects.
                                         Scaled scores are PHRED-like (-10*log10(rank/total)) scaled C-score ranking
                                         a variant relative to all possible substitutions of the
                                         human genome (8.6x10^9).

                                         .. image:: imgs/genomic_scores/CADD_raw_gs.png
                                             :scale: 30
                                             :alt: CADD raw
                                             :align: center

CADD_phred                               Link: https://cadd.gs.washington.edu/download ; Higher values of raw scores
                                         have relative meaning that a variant is more likely to be simulated
                                         (or "not observed") and therefore more likely to have deleterious effects.
                                         Scaled scores are PHRED-like (-10*log10(rank/total)) scaled C-score ranking
                                         a variant relative to all possible substitutions of the
                                         human genome (8.6x10^9).

                                         .. image:: imgs/genomic_scores/CADD_phred_gs.png
                                             :scale: 30
                                             :alt: CADD phred
                                             :align: center

Linsight                                 Linsight scores for prediction of deleterious noncoding variants

                                         .. image:: imgs/genomic_scores/Linsight.png
                                             :scale: 30
                                             :alt: Linsight
                                             :align: center


FitCons i6 merged                        Link: http://compgen.cshl.edu/fitCons/0downloads/tracks/i6/scores/.
                                         Indicates the fraction of genomic positions evincing a particular pattern
                                         (or "fingerprint") of functional assay results, that are under selective
                                         pressure. Score ranges from 0.0 to 1.0. A lower score indicates higher
                                         confidence.

                                         .. image:: imgs/genomic_scores/FitCons-i6-merged.png
                                             :scale: 30
                                             :alt: FitCons-i6-merged
                                             :align: center


Brain Angular Gyrus                      FitCons2 Scores for E067-Brain Angular Gyrus score-Roadmap 
                                         Epigenomics DHS regions

                                         .. image:: imgs/genomic_scores/FitCons2_E067.png
                                             :scale: 30
                                             :alt: FitCons2 E067-Brain Angular Gyrus
                                             :align: center


Brain Anterior Caudate                   Scores for E068-Brain Anterior Caudate score-Roadmap Epigenomics DHS regions

                                         .. figure:: imgs/genomic_scores/FitCons2_E068.png
                                            :scale: 50
                                            :alt: FitCons2 E068-Brain Anterior Caudate
                                            :align: center


Brain Cingulate Gyrus                   Scores for E069-Brain Cingulate Gyrus score-Roadmap Epigenomics DHS regions

                                        .. figure:: imgs/genomic_scores/FitCons2_E069.png
                                           :scale: 50
                                           :alt: FitCons2 E069-Brain Cingulate Gyrus
                                           :align: center


Brain Germinal Matrix                   Scores for E070-Brain Germinal Matrix score-Roadmap Epigenomics DHS regions

                                        .. figure:: imgs/genomic_scores/FitCons2_E070.png
                                           :scale: 50
                                           :alt: FitCons2 E070-Brain Germinal Matrix
                                           :align: center


Brain Hippocampus Middle                Scores for E071-Brain Hippocampus Middle score-Roadmap Epigenomics DHS regions 

                                        .. figure:: imgs/genomic_scores/FitCons2_E071.png
                                           :scale: 50
                                           :alt: FitCons2 E071-Brain Hippocampus Middle
                                           :align: center


Brain Inferior Temporal Lobe            Scores for E072-Brain Inferior Temporal Lobe score-Roadmap Epigenomics DHS regions

                                        .. figure:: imgs/genomic_scores/FitCons2_E072.png
                                           :scale: 50
                                           :alt: FitCons2 E072-Brain Inferior Temporal Lobe
                                           :align: center


Brain Dorsolateral Prefrontal Cortex    Scores for E073-Brain Dorsolateral Prefrontal Cortex score-Roadmap Epigenomics 
                                        DHS regions

                                        .. figure:: imgs/genomic_scores/FitCons2_E073.png
                                           :scale: 50
                                           :alt: FitCons2 E073-Brain Dorsolateral Prefrontal Cortex
                                           :align: center


Brain Substantia Nigra                  Scores for E074-Brain Substantia Nigra score-Roadmap Epigenomics DHS regions

                                        .. figure:: imgs/genomic_scores/FitCons2_E074.png
                                           :scale: 50
                                           :alt: FitCons2 E074-Brain Substantia Nigra
                                           :align: center


Fetal Brain Male                        Scores for E081-Fetal Brain Male score-Roadmap Epigenomics DHS regions
                                        
                                        .. figure:: imgs/genomic_scores/FitCons2_E081.png
                                           :scale: 50
                                           :alt: FitCons2 E081-Fetal Brain Male
                                           :align: center


Fetal Brain Female                      Scores for E082-Fetal Brain Female score-Roadmap Epigenomics DHS regions

                                        .. figure:: imgs/genomic_scores/FitCons2_E082.png
                                           :scale: 50
                                           :alt: FitCons2 E082-Fetal Brain Female
                                           :align: center


SSC Frequency                           SSC Frequency

                                        .. figure:: imgs/genomic_scores/SSC-freq.png
                                           :scale: 50
                                           :alt: SSC Frequency
                                           :align: center


genome gnomAD AC                        Allele counts for the genome-only subset of gnomAD v2.1.


genome gnomAD AN                        Allele numbers for the genome-only subset of gnomAD v2.1.


genome gnomAD AF                        Allele frequencies for the genome-only subset of gnomAD v2.1.
                                        gnomAD v2.1 comprises a total of 16mln SNVs and 1.2mln indels from 125,748 exomes,
                                        and 229mln SNVs and 33mln indels from 15,708 genomes.
                                        (Cited from https://macarthurlab.org/2018/10/17/gnomad-v2-1/)

                                        *"The raw counts (ac and an) refer to the total number of chromosomes with this allele,
                                        and total that were able to be called (whether reference or alternate), respectively.
                                        Thus, the allele frequency is ac/an."*
                                        (Cited from https://macarthurlab.org/2016/03/17/reproduce-all-the-figures-a-users-guide-to-exac-part-2/)

                                        *"Deleterious variants are expected to have lower allele frequencies
                                        than neutral ones, due to negative selection."*
                                        (Cited from the ExAC paper, p.10, 'Inferring variant deleteriousness and gene constraint')

                                        A total of 15,708 genomes.
                                        (Cited from https://gnomad.broadinstitute.org/faq)

                                        .. figure:: imgs/genomic_scores/genome_gnomAD-AF.png
                                           :scale: 50
                                           :alt: genome gnomAD allele frequency
                                           :align: center


genome gnomAD AF percent                Allele frequencies for the genome-only subset of gnomAD v2.1,
                                        as a percentage. (i.e. multiplied by 100.0)

                                        .. figure:: imgs/genomic_scores/genome_gnomAD-AF_percent.png
                                           :scale: 50
                                           :alt: genome gnomAD allele frequency percent
                                           :align: center


genome gnomAD controls AC               Controls-only allele counts for the genome-only subset of gnomAD v2.1.
                                        (Only samples from individuals who were not selected as a case in a 
                                        case/control study of common disease.)


genome gnomAD controls AN               Controls-only allele numbers for the genome-only subset of gnomAD v2.1.
                                        (Only samples from individuals who were not selected as a case in a 
                                        case/control study of common disease.)


genome gnomAD controls AF               Controls-only allele frequencies for the genome-only subset of gnomAD v2.1.
                                        (Only samples from individuals who were not selected as a case in a 
                                        case/control study of common disease.)

                                        .. figure:: imgs/genomic_scores/genome_gnomAD-controls_AF.png
                                           :scale: 50
                                           :alt: controls genome gnomAD allele frequency
                                           :align: center


genome gnomAD controls AF percent       Controls-only allele frequencies for the genome-only subset of gnomAD v2.1,
                                        as a percentage. (i.e. multiplied by 100.0)
                                        (Only samples from individuals who were not selected as a case in a 
                                        case/control study of common disease.)

                                        .. figure:: imgs/genomic_scores/genome_gnomAD-controls_AF_percent.png
                                           :scale: 50
                                           :alt: controls genome gnomAD allele frequency percent
                                           :align: center


genome gnomAD non-neuro AC              Non-neuro allele counts for the genome-only subset of gnomAD v2.1.
                                        (Only samples from individuals who were not ascertained for having a
                                        neurological condition in a neurological case/control study)


genome gnomAD non-neuro AN              Non-neuro allele numbers for the genome-only subset of gnomAD v2.1.
                                        (Only samples from individuals who were not ascertained for having a
                                        neurological condition in a neurological case/control study)


genome gnomAD non-neuro AF              Non-neuro allele frequencies for the genome-only subset of gnomAD v2.1.
                                        (Only samples from individuals who were not ascertained for having a
                                        neurological condition in a neurological case/control study)

                                        .. figure:: imgs/genomic_scores/genome_gnomAD-non_neuro_AF.png
                                           :scale: 50
                                           :alt: non-neuro genome gnomAD allele frequency
                                           :align: center


genome gnomAD non-neuro AF percent      Non-neuro allele frequencies for the genome-only subset of gnomAD v2.1,
                                        as a percentage. (i.e. multiplied by 100.0)
                                        (Only samples from individuals who were not ascertained for having a
                                        neurological condition in a neurological case/control study)

                                        .. figure:: imgs/genomic_scores/genome_gnomAD-non_neuro_AF_percent.png
                                           :scale: 50
                                           :alt: non-neuro genome gnomAD allele frequency percent
                                           :align: center


exome gnomAD AC                         Allele counts for the exome-only subset of gnomAD v2.1.


exome gnomAD AN                         Allele numbers for the exome-only subset of gnomAD v2.1.


exome gnomAD AF                         Allele frequencies for the exome-only subset of gnomAD v2.1.

                                        A total of 125,748 exomes.
                                        (Cited from https://gnomad.broadinstitute.org/faq)

                                        .. figure:: imgs/genomic_scores/exome_gnomAD-AF.png
                                           :scale: 50
                                           :alt: exome gnomAD allele frequency
                                           :align: center


exome gnomAD AF percent                 Allele frequencies for the exome-only subset of gnomAD v2.1,
                                        as a percentage. (i.e. multiplied by 100.0)

                                        .. figure:: imgs/genomic_scores/exome_gnomAD-AF_percent.png
                                           :scale: 50
                                           :alt: exome gnomAD allele frequency percent
                                           :align: center


exome gnomAD controls AC                Controls-only allele counts for the exome-only subset of gnomAD v2.1.
                                        (Only samples from individuals who were not selected as a case in a 
                                        case/control study of common disease.)


exome gnomAD controls AN                Controls-only allele numbers for the exome-only subset of gnomAD v2.1.
                                        (Only samples from individuals who were not selected as a case in a 
                                        case/control study of common disease.)


exome gnomAD controls AF                Controls-only allele frequencies for the exome-only subset of gnomAD v2.1.
                                        (Only samples from individuals who were not selected as a case in a 
                                        case/control study of common disease.)

                                        .. figure:: imgs/genomic_scores/exome_gnomAD-controls_AF.png
                                           :scale: 50
                                           :alt: controls exome gnomAD allele frequency
                                           :align: center


exome gnomAD controls AF percent        Controls-only allele frequencies for the exome-only subset of gnomAD v2.1,
                                        as a percentage. (i.e. multiplied by 100.0)
                                        (Only samples from individuals who were not selected as a case in a 
                                        case/control study of common disease.)

                                        .. figure:: imgs/genomic_scores/exome_gnomAD-controls_AF_percent.png
                                           :scale: 50
                                           :alt: controls exome gnomAD allele frequency percent
                                           :align: center


exome gnomAD non-neuro AC               Non-neuro allele counts for the exome-only subset of gnomAD v2.1.
                                        (Only samples from individuals who were not ascertained for having a
                                        neurological condition in a neurological case/control study)


exome gnomAD non-neuro AN               Non-neuro allele numbers for the exome-only subset of gnomAD v2.1.
                                        (Only samples from individuals who were not ascertained for having a
                                        neurological condition in a neurological case/control study)


exome gnomAD non-neuro AF               Non-neuro allele frequencies for the exome-only subset of gnomAD v2.1.
                                        (Only samples from individuals who were not ascertained for having a
                                        neurological condition in a neurological case/control study)

                                        .. figure:: imgs/genomic_scores/exome_gnomAD-non_neuro_AF.png
                                           :scale: 50
                                           :alt: non-neuro exome gnomAD allele frequency
                                           :align: center


exome gnomAD non-neuro AF percent       Non-neuro allele frequencies for the exome-only subset of gnomAD v2.1,
                                        as a percentage. (i.e. multiplied by 100.0)
                                        (Only samples from individuals who were not ascertained for having a
                                        neurological condition in a neurological case/control study)

                                        .. figure:: imgs/genomic_scores/exome_gnomAD-non_neuro_AF_percent.png
                                           :scale: 50
                                           :alt: non-neuro exome gnomAD allele frequency percent
                                           :align: center


MPC                                     MPC - Missense badness, PolyPhen-2, and Constraint

                                        - `MPC paper`_
                                        - `MPC paper supplement`_

                                        Downloaded from: `MPC download link`_

                                        .. figure:: imgs/genomic_scores/MPC.png
                                           :scale: 50
                                           :alt: MPC
                                           :align: center
====================================    ========================================================================================================

.. _`MPC download link`: ftp://ftp.broadinstitute.org/pub/ExAC_release/release1/regional_missense_constraint/fordist_constraint_official_mpc_values_v2.txt.gz
.. _`MPC paper`: https://www.biorxiv.org/content/biorxiv/early/2017/06/12/148353.full.pdf
.. _`MPC paper supplement`: https://www.biorxiv.org/content/biorxiv/suppl/2017/06/12/148353.DC1/148353-1.pdf

