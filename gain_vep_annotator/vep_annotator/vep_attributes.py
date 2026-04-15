
full_attributes = {
    "Location": (
        "str",
        "Location of variant in standard "
        "coordinate format (chr:start or chr:start-end)",
    ),
    "Allele": (
        "str",
        "The variant allele used to calculate the consequence",
    ),
    "Gene": (
        "str",
        "Stable ID of affected gene",
    ),
    "Feature": (
        "str",
        "Stable ID of feature",
    ),
    "Feature_type": (
        "str",
        "Type of feature - Transcript, "
        "RegulatoryFeature or MotifFeature",
    ),
    "Consequence": (
        "str",
        "Consequence type",
    ),
    "cDNA_position": (
        "str",
        "Relative position of base pair in cDNA sequence",
    ),
    "CDS_position": (
        "str",
        "Relative position of base pair in coding sequence",
    ),
    "Protein_position": (
        "str",
        "Relative position of amino acid in protein",
    ),
    "Amino_acids": (
        "str",
        "Reference and variant amino acids",
    ),
    "Codons": (
        "str",
        "Reference and variant codon sequence",
    ),
    "Existing_variation": (
        "str",
        "Identifier(s) of co-located known variants",
    ),
    "IMPACT": (
        "str",
        "Subjective impact classification of consequence type",
    ),
    "DISTANCE": (
        "str",
        "Shortest distance from variant to transcript",
    ),
    "STRAND": (
        "str",
        "Strand of the feature (1/-1)",
    ),
    "FLAGS": (
        "str",
        "Transcript quality flags",
    ),
    "VARIANT_CLASS": (
        "str",
        "SO variant class",
    ),
    "SYMBOL": (
        "str",
        "Gene symbol (e.g. HGNC)",
    ),
    "SYMBOL_SOURCE": (
        "str",
        "Source of gene symbol",
    ),
    "HGNC_ID": (
        "str",
        "Stable identifer of HGNC gene symbol",
    ),
    "BIOTYPE": (
        "str",
        "Biotype of transcript or regulatory feature",
    ),
    "CANONICAL": (
        "str",
        "Indicates if transcript is canonical for this gene",
    ),
    "MANE": (
        "str",
        "MANE (Matched Annotation from NCBI and EMBL-EBI) "
        "set(s) the transcript belongs to",
    ),
    "MANE_SELECT": (
        "str",
        "MANE Select (Matched Annotation "
        "from NCBI and EMBL-EBI) Transcript",
    ),
    "MANE_PLUS_CLINICAL": (
        "str",
        "MANE Plus Clinical (Matched Annotation "
        "from NCBI and EMBL-EBI) Transcript",
    ),
    "TSL": (
        "str",
        "Transcript support level",
    ),
    "APPRIS": (
        "str",
        "Annotates alternatively spliced transcripts as primary "
        "or alternate based on a range of computational methods",
    ),
    "CCDS": (
        "str",
        "Indicates if transcript is a CCDS transcript",
    ),
    "ENSP": (
        "str",
        "Protein identifer",
    ),
    "SWISSPROT": (
        "str",
        "UniProtKB/Swiss-Prot accession",
    ),
    "TREMBL": (
        "str",
        "UniProtKB/TrEMBL accession",
    ),
    "UNIPARC": (
        "str",
        "UniParc accession",
    ),
    "UNIPROT_ISOFORM": (
        "str",
        "Direct mappings to UniProtKB isoforms",
    ),
    "GENE_PHENO": (
        "str",
        "Indicates if gene is associated with "
        "a phenotype, disease or trait",
    ),
    "SIFT": (
        "str",
        "SIFT prediction and/or score",
    ),
    "PolyPhen": (
        "str",
        "PolyPhen prediction and/or score",
    ),
    "EXON": (
        "str",
        "Exon number(s) / total",
    ),
    "INTRON": (
        "str",
        "Intron number(s) / total",
    ),
    "DOMAINS": (
        "str",
        "The source and identifer of "
        "any overlapping protein domains",
    ),
    "miRNA": (
        "str",
        "SO terms of overlapped miRNA "
        "secondary structure feature(s)",
    ),
    "HGVSc": (
        "str",
        "HGVS coding sequence name",
    ),
    "HGVSp": (
        "str",
        "HGVS protein sequence name",
    ),
    "HGVS_OFFSET": (
        "str",
        "Indicates by how many bases the "
        "HGVS notations for this variant have been shifted",
    ),
    "AF": (
        "str",
        "Frequency of existing variant in "
        "1000 Genomes combined population",
    ),
    "AFR_AF": (
        "str",
        "Frequency of existing variant in "
        "1000 Genomes combined African population",
    ),
    "AMR_AF": (
        "str",
        "Frequency of existing variant in "
        "1000 Genomes combined American population",
    ),
    "EAS_AF": (
        "str",
        "Frequency of existing variant in "
        "1000 Genomes combined East Asian population",
    ),
    "EUR_AF": (
        "str",
        "Frequency of existing variant in "
        "1000 Genomes combined European population",
    ),
    "SAS_AF": (
        "str",
        "Frequency of existing variant in "
        "1000 Genomes combined South Asian population",
    ),
    "gnomADe_AF": (
        "str",
        "Frequency of existing variant in "
        "gnomAD exomes combined population",
    ),
    "gnomADe_AFR_AF": (
        "str",
        "Frequency of existing variant in "
        "gnomAD exomes African/American population",
    ),
    "gnomADe_AMR_AF": (
        "str",
        "Frequency of existing variant in "
        "gnomAD exomes American population",
    ),
    "gnomADe_ASJ_AF": (
        "str",
        "Frequency of existing variant in "
        "gnomAD exomes Ashkenazi Jewish population",
    ),
    "gnomADe_EAS_AF": (
        "str",
        "Frequency of existing variant in "
        "gnomAD exomes East Asian population",
    ),
    "gnomADe_FIN_AF": (
        "str",
        "Frequency of existing variant in "
        "gnomAD exomes Finnish population",
    ),
    "gnomADe_MID_AF": (
        "str",
        "Frequency of existing variant in "
        "gnomAD exomes Mid-eastern population",
    ),
    "gnomADe_NFE_AF": (
        "str",
        "Frequency of existing variant in "
        "gnomAD exomes Non-Finnish European population",
    ),
    "gnomADe_OTH_AF": (
        "str",
        "Frequency of existing variant in "
        "gnomAD exomes other combined populations",
    ),
    "gnomADe_SAS_AF": (
        "str",
        "Frequency of existing variant in "
        "gnomAD exomes South Asian population",
    ),
    "gnomADe_REMAINING_AF": (
        "str",
        "Frequency of existing variant in "
        "gnomAD exomes remaining combined populations",
    ),
    "gnomADg_AF": (
        "str",
        "Frequency of existing variant in "
        "gnomAD genomes combined population",
    ),
    "gnomADg_AFR_AF": (
        "str",
        "Frequency of existing variant in "
        "gnomAD genomes African/American population",
    ),
    "gnomADg_AMI_AF": (
        "str",
        "Frequency of existing variant in "
        "gnomAD genomes Amish population",
    ),
    "gnomADg_AMR_AF": (
        "str",
        "Frequency of existing variant in "
        "gnomAD genomes American population",
    ),
    "gnomADg_ASJ_AF": (
        "str",
        "Frequency of existing variant in "
        "gnomAD genomes Ashkenazi Jewish population",
    ),
    "gnomADg_EAS_AF": (
        "str",
        "Frequency of existing variant in "
        "gnomAD genomes East Asian population",
    ),
    "gnomADg_FIN_AF": (
        "str",
        "Frequency of existing variant in "
        "gnomAD genomes Finnish population",
    ),
    "gnomADg_MID_AF": (
        "str",
        "Frequency of existing variant in "
        "gnomAD genomes Mid-eastern population",
    ),
    "gnomADg_NFE_AF": (
        "str",
        "Frequency of existing variant in "
        "gnomAD genomes Non-Finnish European population",
    ),
    "gnomADg_OTH_AF": (
        "str",
        "Frequency of existing variant in "
        "gnomAD genomes other combined populations",
    ),
    "gnomADg_SAS_AF": (
        "str",
        "Frequency of existing variant in "
        "gnomAD genomes South Asian population",
    ),
    "gnomADg_REMAINING_AF": (
        "str",
        "Frequency of existing variant in "
        "gnomAD genomes remaining combined populations",
    ),
    "MAX_AF": (
        "str",
        "Maximum observed allele frequency in "
        "1000 Genomes, ESP and ExAC/gnomAD",
    ),
    "MAX_AF_POPS": (
        "str",
        "Populations in which maximum "
        "allele frequency was observed",
    ),
    "CLIN_SIG": (
        "str",
        "ClinVar clinical significance of the dbSNP variant",
    ),
    "SOMATIC": (
        "str",
        "Somatic status of existing variant",
    ),
    "PHENO": (
        "str",
        "Indicates if existing variant(s) is associated with "
        "a phenotype, disease or trait; "
        "multiple values correspond to multiple variants",
    ),
    "PUBMED": (
        "str",
        "Pubmed ID(s) of publications that cite existing variant",
    ),
    "MOTIF_NAME": (
        "str",
        "The stable identifier of a transcription factor "
        "binding profile (TFBP) aligned at this position",
    ),
    "MOTIF_POS": (
        "str",
        "The relative position of the "
        "variation in the aligned TFBP",
    ),
    "HIGH_INF_POS": (
        "str",
        "A flag indicating if the variant falls in a "
        "high information position of the TFBP",
    ),
    "MOTIF_SCORE_CHANGE": (
        "str",
        "The difference in motif score of the reference "
        "and variant sequences for the TFBP",
    ),
    "TRANSCRIPTION_FACTORS": (
        "str",
        "List of transcription factors which bind to "
        "the transcription factor binding profile",
    ),
    "worst_consequence": (
        "str", "Worst consequence reported by VEP",
    ),
    "highest_impact": ("str", "Highest impact reported by VEP"),
    "gene_consequence": (
        "str", "List of gene consequence pairs reported by VEP",
    ),
}

effect_attributes = {
    "Location": (
        "str",
        "Location of variant in standard "
        "coordinate format (chr:start or chr:start-end)",
    ),
    "Allele": (
        "str",
        "The variant allele used to calculate the consequence",
    ),
    "Gene": (
        "str",
        "Stable ID of affected gene",
    ),
    "Feature": (
        "str",
        "Stable ID of feature",
    ),
    "Feature_type": (
        "str",
        "Type of feature - Transcript, "
        "RegulatoryFeature or MotifFeature",
    ),
    "Consequence": (
        "str",
        "Consequence type",
    ),
    "cDNA_position": (
        "str",
        "Relative position of base pair in cDNA sequence",
    ),
    "CDS_position": (
        "str",
        "Relative position of base pair in coding sequence",
    ),
    "Protein_position": (
        "str",
        "Relative position of amino acid in protein",
    ),
    "Amino_acids": (
        "str",
        "Reference and variant amino acids",
    ),
    "Codons": (
        "str",
        "Reference and variant codon sequence",
    ),
    "Existing_variation": (
        "str",
        "Identifier(s) of co-located known variants",
    ),
    "IMPACT": (
        "str",
        "Subjective impact classification of consequence type",
    ),
    "DISTANCE": (
        "str",
        "Shortest distance from variant to transcript",
    ),
    "STRAND": (
        "str",
        "Strand of the feature (1/-1)",
    ),
    "FLAGS": (
        "str",
        "Transcript quality flags",
    ),
    "SYMBOL": (
        "str",
        "Gene symbol (e.g. HGNC)",
    ),
    "SYMBOL_SOURCE": (
        "str",
        "Source of gene symbol",
    ),
    "HGNC_ID": (
        "str",
        "Stable identifer of HGNC gene symbol",
    ),
    "SOURCE": (
        "str",
        "Source of transcript",
    ),
    "worst_consequence": (
        "str", "Worst consequence reported by VEP",
    ),
    "highest_impact": ("str", "Highest impact reported by VEP"),
    "gene_consequence": (
        "str", "List of gene consequence pairs reported by VEP",
    ),
}
