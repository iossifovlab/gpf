
full_attributes = {
    "Location": (
        "object",
        "Location of variant in standard "
        "coordinate format (chr:start or chr:start-end)",
    ),
    "Allele": (
        "object",
        "The variant allele used to calculate the consequence",
    ),
    "Gene": (
        "object",
        "Stable ID of affected gene",
    ),
    "Feature": (
        "object",
        "Stable ID of feature",
    ),
    "Feature_type": (
        "object",
        "Type of feature - Transcript, "
        "RegulatoryFeature or MotifFeature",
    ),
    "Consequence": (
        "object",
        "Consequence type",
    ),
    "cDNA_position": (
        "object",
        "Relative position of base pair in cDNA sequence",
    ),
    "CDS_position": (
        "object",
        "Relative position of base pair in coding sequence",
    ),
    "Protein_position": (
        "object",
        "Relative position of amino acid in protein",
    ),
    "Amino_acids": (
        "object",
        "Reference and variant amino acids",
    ),
    "Codons": (
        "object",
        "Reference and variant codon sequence",
    ),
    "Existing_variation": (
        "object",
        "Identifier(s) of co-located known variants",
    ),
    "IMPACT": (
        "object",
        "Subjective impact classification of consequence type",
    ),
    "DISTANCE": (
        "object",
        "Shortest distance from variant to transcript",
    ),
    "STRAND": (
        "object",
        "Strand of the feature (1/-1)",
    ),
    "FLAGS": (
        "object",
        "Transcript quality flags",
    ),
    "VARIANT_CLASS": (
        "object",
        "SO variant class",
    ),
    "SYMBOL": (
        "object",
        "Gene symbol (e.g. HGNC)",
    ),
    "SYMBOL_SOURCE": (
        "object",
        "Source of gene symbol",
    ),
    "HGNC_ID": (
        "object",
        "Stable identifer of HGNC gene symbol",
    ),
    "BIOTYPE": (
        "object",
        "Biotype of transcript or regulatory feature",
    ),
    "CANONICAL": (
        "object",
        "Indicates if transcript is canonical for this gene",
    ),
    "MANE_SELECT": (
        "object",
        "MANE Select (Matched Annotation "
        "from NCBI and EMBL-EBI) Transcript",
    ),
    "MANE_PLUS_CLINICAL": (
        "object",
        "MANE Plus Clinical (Matched Annotation "
        "from NCBI and EMBL-EBI) Transcript",
    ),
    "TSL": (
        "object",
        "Transcript support level",
    ),
    "APPRIS": (
        "object",
        "Annotates alternatively spliced transcripts as primary "
        "or alternate based on a range of computational methods",
    ),
    "CCDS": (
        "object",
        "Indicates if transcript is a CCDS transcript",
    ),
    "ENSP": (
        "object",
        "Protein identifer",
    ),
    "SWISSPROT": (
        "object",
        "UniProtKB/Swiss-Prot accession",
    ),
    "TREMBL": (
        "object",
        "UniProtKB/TrEMBL accession",
    ),
    "UNIPARC": (
        "object",
        "UniParc accession",
    ),
    "UNIPROT_ISOFORM": (
        "object",
        "Direct mappings to UniProtKB isoforms",
    ),
    "GENE_PHENO": (
        "object",
        "Indicates if gene is associated with "
        "a phenotype, disease or trait",
    ),
    "SIFT": (
        "object",
        "SIFT prediction and/or score",
    ),
    "PolyPhen": (
        "object",
        "PolyPhen prediction and/or score",
    ),
    "EXON": (
        "object",
        "Exon number(s) / total",
    ),
    "INTRON": (
        "object",
        "Intron number(s) / total",
    ),
    "DOMAINS": (
        "object",
        "The source and identifer of "
        "any overlapping protein domains",
    ),
    "miRNA": (
        "object",
        "SO terms of overlapped miRNA "
        "secondary structure feature(s)",
    ),
    "HGVSc": (
        "object",
        "HGVS coding sequence name",
    ),
    "HGVSp": (
        "object",
        "HGVS protein sequence name",
    ),
    "HGVS_OFFSET": (
        "object",
        "Indicates by how many bases the "
        "HGVS notations for this variant have been shifted",
    ),
    "AF": (
        "object",
        "Frequency of existing variant in "
        "1000 Genomes combined population",
    ),
    "AFR_AF": (
        "object",
        "Frequency of existing variant in "
        "1000 Genomes combined African population",
    ),
    "AMR_AF": (
        "object",
        "Frequency of existing variant in "
        "1000 Genomes combined American population",
    ),
    "EAS_AF": (
        "object",
        "Frequency of existing variant in "
        "1000 Genomes combined East Asian population",
    ),
    "EUR_AF": (
        "object",
        "Frequency of existing variant in "
        "1000 Genomes combined European population",
    ),
    "SAS_AF": (
        "object",
        "Frequency of existing variant in "
        "1000 Genomes combined South Asian population",
    ),
    "gnomADe_AF": (
        "object",
        "Frequency of existing variant in "
        "gnomAD exomes combined population",
    ),
    "gnomADe_AFR_AF": (
        "object",
        "Frequency of existing variant in "
        "gnomAD exomes African/American population",
    ),
    "gnomADe_AMR_AF": (
        "object",
        "Frequency of existing variant in "
        "gnomAD exomes American population",
    ),
    "gnomADe_ASJ_AF": (
        "object",
        "Frequency of existing variant in "
        "gnomAD exomes Ashkenazi Jewish population",
    ),
    "gnomADe_EAS_AF": (
        "object",
        "Frequency of existing variant in "
        "gnomAD exomes East Asian population",
    ),
    "gnomADe_FIN_AF": (
        "object",
        "Frequency of existing variant in "
        "gnomAD exomes Finnish population",
    ),
    "gnomADe_NFE_AF": (
        "object",
        "Frequency of existing variant in "
        "gnomAD exomes Non-Finnish European population",
    ),
    "gnomADe_OTH_AF": (
        "object",
        "Frequency of existing variant in "
        "gnomAD exomes other combined populations",
    ),
    "gnomADe_SAS_AF": (
        "object",
        "Frequency of existing variant in "
        "gnomAD exomes South Asian population",
    ),
    "gnomADg_AF": (
        "object",
        "Frequency of existing variant in "
        "gnomAD genomes combined population",
    ),
    "gnomADg_AFR_AF": (
        "object",
        "Frequency of existing variant in "
        "gnomAD genomes African/American population",
    ),
    "gnomADg_AMI_AF": (
        "object",
        "Frequency of existing variant in "
        "gnomAD genomes Amish population",
    ),
    "gnomADg_AMR_AF": (
        "object",
        "Frequency of existing variant in "
        "gnomAD genomes American population",
    ),
    "gnomADg_ASJ_AF": (
        "object",
        "Frequency of existing variant in "
        "gnomAD genomes Ashkenazi Jewish population",
    ),
    "gnomADg_EAS_AF": (
        "object",
        "Frequency of existing variant in "
        "gnomAD genomes East Asian population",
    ),
    "gnomADg_FIN_AF": (
        "object",
        "Frequency of existing variant in "
        "gnomAD genomes Finnish population",
    ),
    "gnomADg_MID_AF": (
        "object",
        "Frequency of existing variant in "
        "gnomAD genomes Mid-eastern population",
    ),
    "gnomADg_NFE_AF": (
        "object",
        "Frequency of existing variant in "
        "gnomAD genomes Non-Finnish European population",
    ),
    "gnomADg_OTH_AF": (
        "object",
        "Frequency of existing variant in "
        "gnomAD genomes other combined populations",
    ),
    "gnomADg_SAS_AF": (
        "object",
        "Frequency of existing variant in "
        "gnomAD genomes South Asian population",
    ),
    "MAX_AF": (
        "object",
        "Maximum observed allele frequency in "
        "1000 Genomes, ESP and ExAC/gnomAD",
    ),
    "MAX_AF_POPS": (
        "object",
        "Populations in which maximum "
        "allele frequency was observed",
    ),
    "CLIN_SIG": (
        "object",
        "ClinVar clinical significance of the dbSNP variant",
    ),
    "SOMATIC": (
        "object",
        "Somatic status of existing variant",
    ),
    "PHENO": (
        "object",
        "Indicates if existing variant(s) is associated with "
        "a phenotype, disease or trait; "
        "multiple values correspond to multiple variants",
    ),
    "PUBMED": (
        "object",
        "Pubmed ID(s) of publications that cite existing variant",
    ),
    "MOTIF_NAME": (
        "object",
        "The stable identifier of a transcription factor "
        "binding profile (TFBP) aligned at this position",
    ),
    "MOTIF_POS": (
        "object",
        "The relative position of the "
        "variation in the aligned TFBP",
    ),
    "HIGH_INF_POS": (
        "object",
        "A flag indicating if the variant falls in a "
        "high information position of the TFBP",
    ),
    "MOTIF_SCORE_CHANGE": (
        "object",
        "The difference in motif score of the reference "
        "and variant sequences for the TFBP",
    ),
    "TRANSCRIPTION_FACTORS": (
        "object",
        "List of transcription factors which bind to "
        "the transcription factor binding profile",
    ),
    "worst_consequence": (
        "object", "Worst consequence reported by VEP",
    ),
    "highest_impact": ("object", "Highest impact reported by VEP"),
    "gene_consequence": (
        "object", "List of gene consequence pairs reported by VEP",
    ),
}

effect_attributes = {
    "Location": (
        "object",
        "Location of variant in standard "
        "coordinate format (chr:start or chr:start-end)",
    ),
    "Allele": (
        "object",
        "The variant allele used to calculate the consequence",
    ),
    "Gene": (
        "object",
        "Stable ID of affected gene",
    ),
    "Feature": (
        "object",
        "Stable ID of feature",
    ),
    "Feature_type": (
        "object",
        "Type of feature - Transcript, "
        "RegulatoryFeature or MotifFeature",
    ),
    "Consequence": (
        "object",
        "Consequence type",
    ),
    "cDNA_position": (
        "object",
        "Relative position of base pair in cDNA sequence",
    ),
    "CDS_position": (
        "object",
        "Relative position of base pair in coding sequence",
    ),
    "Protein_position": (
        "object",
        "Relative position of amino acid in protein",
    ),
    "Amino_acids": (
        "object",
        "Reference and variant amino acids",
    ),
    "Codons": (
        "object",
        "Reference and variant codon sequence",
    ),
    "Existing_variation": (
        "object",
        "Identifier(s) of co-located known variants",
    ),
    "IMPACT": (
        "object",
        "Subjective impact classification of consequence type",
    ),
    "DISTANCE": (
        "object",
        "Shortest distance from variant to transcript",
    ),
    "STRAND": (
        "object",
        "Strand of the feature (1/-1)",
    ),
    "FLAGS": (
        "object",
        "Transcript quality flags",
    ),
    "SYMBOL": (
        "object",
        "Gene symbol (e.g. HGNC)",
    ),
    "SYMBOL_SOURCE": (
        "object",
        "Source of gene symbol",
    ),
    "HGNC_ID": (
        "object",
        "Stable identifer of HGNC gene symbol",
    ),
    "SOURCE": (
        "object",
        "Source of transcript",
    ),
    "worst_consequence": (
        "object", "Worst consequence reported by VEP",
    ),
    "highest_impact": ("object", "Highest impact reported by VEP"),
    "gene_consequence": (
        "object", "List of gene consequence pairs reported by VEP",
    ),
}
