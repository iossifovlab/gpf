# Test Plan for Allele Liftover Function

## Objective
Verify the correctness of the `bcf_liftover_allele` function in `dae/dae/annotation/liftover_annotator.py` against the scenarios described in the BCFtools/liftover paper (Bioinformatics, 2024).

## Test Scenarios

### 1. Simple SNV Liftover (Baseline)
*   **Description:** Standard SNV where source Reference matches target Reference.
*   **Input:** `chrA:2 A>T` (Source Ref: A, Target Ref: A)
*   **Expected:** `chrB:2 A>T`

### 2. Strand Change
*   **Description:** Target region is on the negative strand relative to source.
*   **Setup:** Chain file maps `chrA` (+) to `chrB` (-).
*   **Input:** `chrA:2 A>T`
*   **Expected:** `chrB:11 T>A` (Coordinates inverted, Alleles reverse complemented)

### 3. Reference/Alternate Allele Swap
*   **Description:** Source Reference matches Target Alternate, and Source Alternate matches Target Reference.
*   **Setup:** Target genome has the "Alternate" allele at the mapped position.
*   **Input:** `chrA:2 A>T` (Source Ref: A, Target Ref: T)
*   **Expected:** `chrB:2 T>A` (Alleles swapped)

### 4. Strand Change + Ref/Alt Swap
*   **Description:** Combination of strand change and allele swap.
*   **Setup:** Chain maps to negative strand. Target Ref matches Source Alt (reverse complemented).
*   **Input:** `chrA:2 A>T`
*   **Expected:** `chrB:11 A>T` (Reverse complement of A>T is T>A. Swap T>A is A>T).

### 5. Indel Normalization & Extension
*   **Description:** Indel requiring normalization and anchor verification.
*   **Input:** `chrA:2 A>AT` (Insertion)
*   **Expected:** Mapped correctly using flanking anchors.

### 6. Ref Mismatch (Failure Case)
*   **Description:** Source Ref does not match Target Ref, and Source Alt does not match Target Ref.
*   **Input:** `chrA:2 A>T` (Target Ref: G)
*   **Expected:** `None`

### 7. Chain Gap (Failure Case)
*   **Description:** Variant falls into a region with no chain mapping.
*   **Input:** Coordinate not in chain file.
*   **Expected:** `None`

### 8. Internal Chain Gap (Failure Case)
*   **Description:** Variant falls into a gap within a chain alignment (Source has sequence not present in Target).
*   **Input:** Coordinate in the source gap.
*   **Expected:** `None`
