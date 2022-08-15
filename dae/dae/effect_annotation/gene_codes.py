class NuclearCode:
    """Defines codon to amino acid translation codes."""

    # pylint: disable=too-few-public-methods
    stopCodons = ["TAG", "TAA", "TGA"]
    startCodons = ["ATG"]

    CodonsAa = {
        "Gly": ["GGG", "GGA", "GGT", "GGC"],
        "Glu": ["GAG", "GAA"],
        "Asp": ["GAT", "GAC"],
        "Val": ["GTG", "GTA", "GTT", "GTC"],
        "Ala": ["GCG", "GCA", "GCT", "GCC"],
        "Arg": ["AGG", "AGA", "CGG", "CGA", "CGT", "CGC"],
        "Ser": ["AGT", "AGC", "TCG", "TCA", "TCT", "TCC"],
        "Lys": ["AAG", "AAA"],
        "Asn": ["AAT", "AAC"],
        "Met": startCodons,
        "Ile": ["ATA", "ATT", "ATC"],
        "Thr": ["ACG", "ACA", "ACT", "ACC"],
        "Trp": ["TGG"],
        "End": stopCodons,
        "Cys": ["TGT", "TGC"],
        "Tyr": ["TAT", "TAC"],
        "Leu": ["TTG", "TTA", "CTG", "CTA", "CTT", "CTC"],
        "Phe": ["TTT", "TTC"],
        "Gln": ["CAG", "CAA"],
        "His": ["CAT", "CAC"],
        "Pro": ["CCG", "CCA", "CCT", "CCC"],
    }

    CodonsAaKeys = list(CodonsAa.keys())
