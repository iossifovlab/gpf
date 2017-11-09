# Supported effect types (in order of priority):
## Coding
* First, a check is preformed if the transcript model is for coding or non-coding region. All variants in non-coding are marked as **non-coding**

## Splice site
* Every modification in splice site regions is marked as **splice-site**, even if it results in the same nucleotides
* This includes splice sites in UTR regions

## noStart
* All modifications in start codon are marked as noStart, even if it results in a new start codon.

## noStop
* All modifications(excluding synonymous substitutions) in stop codon are marked as noEnd, even if it results in a new start codon.

## Frame-shift
Possible effect types when there is an indel are:
* **frame-shift** - inserted/deleted nucleotides count is not divisible by 3
* **no-frame-shift** - inserted/deleted nucleotides count is divisible by 3
* **no-frame-shift-newStop** - inserted/deleted nucleotides count is not divisible by 3 and there is a premature stop codon

## Substitutions
Possible effect types when there is a simple or complex substitution(but the count of the nucleotides is the same in the reference and resulting sequence) are:
* **missense** - at least one of the changed codons codes for a different amino acid then before
* **nonsense** - one of affected codons is a premature stop codon
* **synonymous** - all affected codons code for the same amino acids as before

## UTR
* **3'UTR**/**5'UTR** - Modified exonic UTR regions
* **3'UTR-intron**/**5'UTR-intron** - Modified intronic UTR regions

## Intron
* Modifications in the introns(outside splice sites) are marked as **intron**

# Effect details
## Protein length
* Protein length is always available, except for integenic effect type

## Position inside protein
Position inside protein is available for:
* frame-shift/no-frame-shift/substitutions - shows the position of the first affected codon
* Intron/Splice-site - shows the position of the first codon after the variant position
* noStart - always is 1
* noEnd - The last codon is marked as one plus the protein length, resulting the somewhat odd result of, for example, 100/99

## Amino acids change
##### Available for:
* no-frame-shift
* substitutions

## Intron distances
##### Available for:
* splice-site
* intron

##### Information available:
* dist_from_acceptor - number of nucleotides from the variant to the acceptor side
* dist_from_donor - number of nucleotides from the variant to the donor side
* dist_from_coding - the shortest of dist_from_acceptor and dist_from_donor

## Intron details:
##### Available for:
* splice-site
* intron

##### Information available:
* which_intron - in which intron region is the variant
* how_many_introns - total intron regions count
* intron_length - the length of the affected intron region
