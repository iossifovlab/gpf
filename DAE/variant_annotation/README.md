# Supported effect types (in order of priority):
## Coding
* First, a check is preformed if the transcript model is for coding or non-coding region. All variants in non-coding are marked as **non-coding**

## Splice site
* Every modification in splice site regions is marked as **splice-site**, even if it results in the same nucleotides
* This includes splice sites in UTR regions

## noStart
* All modifications in start codon are marked as noStart, even if it results in a new start codon.

## noStop
Modifications in stop codon can result in:
* **noStop** - if the stop codon has been removed
* **no-frame-shift** - if the resulting sequence still contains a stop codon and the inserted/deleted nucleotides count before the stop codon is divisible by 3
* **frame-shift** - if the indel is not divisible by 3, it wil be marked as frame-shift and the resulting sequence won't be checked for stop codons
* **3'UTR** - if the the resulting sequence still contains a stop codon and the inserted/deleted nucleotides are after the stop codon
* **integenic** - Same as above if there is no 3'UTR region

## Frame-shift
Possible effect types when there is an indel are:
* **frame-shift** - inserted/deleted nucleotides count is not divisible by 3
* **no-frame-shift** - inserted/deleted nucleotides count is divisible by 3
* **no-frame-shift-newStop** - inserted/deleted nucleotides count is not divisible by 3 and there is a premature stop codon

## Protein Change
Possible effect types when there is a simple or complex substitution(but the nucleotides is the same in the reference and resulting sequence) are:
* **missense** - at least one of the changed codons codes for a different amino acid then before
* **nonsense** - one of affected codons is a premature stop codon
* **synynomous** - all affected codons code for the same amino acids as before

## UTR
* **3'UTR**/**5'UTR** - Modified exonic UTR regions
* **3'UTR-intron**/**5'UTR-intron** - Modified intronic UTR regions

## Intron
* Modifications in the introns(outside splice sites) are marked as **intron**

# Effect details
### Protein length
* Protein length is always available, except for integenic effect type

### Position inside protein
Position inside protein is available for:
* Protein changes - shows the position of the first affected codon
* Intron/Splice-site - shows the position of the first codon after the variant position
* noStart - always is 1
* noEnd - The last codon is marked as one plus the protein length, resulting the somewhat odd result of, for example, 100/99 
