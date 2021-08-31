export class SummaryAllele {
  public location: string;
  public position: number;
  public endPosition: number;
  public chrom: string;
  public variant: string;
  public effect: string;
  public frequency: number;
  public numberOfFamilyVariants: number;
  public seenAsDenovo: boolean;

  public seenInAffected: boolean;
  public seenInUnaffected: boolean;
  public svuid: string;
  public sauid: string;

  // TODO: Use effecttypes.ts
  public readonly lgds = ['nonsense', 'splice-site', 'frame-shift', 'no-frame-shift-new-stop'];

  public static comparator(a: SummaryAllele, b: SummaryAllele) {
    if (a.comparisonValue > b.comparisonValue) {
      return 1;
    } else if (a.comparisonValue < b.comparisonValue) {
      return -1;
    } else {
      return 0;
    }
  }

  public static fromRow(row: object, svuid?: string): SummaryAllele {
    const result = new SummaryAllele();
    result.location = row['location'];
    result.position = row['position'];
    result.endPosition = row['end_position'];
    result.chrom = row['chrom'];
    result.variant = row['variant'];
    result.effect = row['effect'];
    result.frequency = row['frequency'];
    result.numberOfFamilyVariants = row['family_variants_count'];
    result.seenAsDenovo = row['is_denovo'];
    result.seenInAffected = row['seen_in_affected'];
    result.seenInUnaffected = row['seen_in_unaffected'];
    result.sauid = result.location + ':' + result.variant;
    result.svuid = svuid ? svuid : result.sauid;
    return result;
  }

  public isLGDs(): boolean {
    return (this.lgds.indexOf(this.effect) !== -1 || this.effect === 'lgds');
  }

  public isMissense(): boolean {
    return (this.effect === 'missense');
  }

  public isSynonymous(): boolean {
    return (this.effect === 'synonymous');
  }

  public isCNVPlus(): boolean {
    return (this.effect === 'CNV+');
  }

  public isCNVPMinus(): boolean {
    return (this.effect === 'CNV-');
  }

  public isCNV(): boolean {
    return this.isCNVPlus() || this.isCNVPMinus();
  }

  get comparisonValue(): number {
    let sum = 0;
    sum += this.seenAsDenovo && !this.isCNV() ? 200 : 100;
    sum += this.isLGDs() ? 50 : this.isMissense() ? 40 : this.isSynonymous() ? 30 : !this.isCNV() ? 20 : this.seenAsDenovo ? 10 : 5;
    sum += (this.seenInAffected && this.seenInUnaffected) ? 1 : this.seenInUnaffected ? 2 : 3;
    return sum;
  }

  public intersects(allele: SummaryAllele): boolean {
    if (!this.isCNV()) {
      this.endPosition = this.position;
    }

    if (!allele.isCNV()) {
      allele.endPosition = allele.position;
    }

    return !(this.position >= allele.endPosition || this.endPosition <= allele.position);
  }
}

export class SummaryAllelesArray {

  public readonly summaryAlleles: SummaryAllele[] = [];
  public readonly summaryAlleleIds: string[] = [];

  public addSummaryRow(row: object) {
    if (!row) {
      return;
    }
    for (const alleleRow of row['alleles']) {
      if (alleleRow) {
        this.addSummaryAllele(SummaryAllele.fromRow(alleleRow));
      }
    }
  }

  public addSummaryAllele(summaryAllele: SummaryAllele) {
    const alleleIndex = this.summaryAlleleIds.indexOf(summaryAllele.sauid);
    if (alleleIndex !== -1) {
      this.summaryAlleles[alleleIndex].numberOfFamilyVariants =
        this.summaryAlleles[alleleIndex].numberOfFamilyVariants +
        summaryAllele.numberOfFamilyVariants;

      this.summaryAlleles[alleleIndex].seenAsDenovo =
        this.summaryAlleles[alleleIndex].seenAsDenovo || summaryAllele.seenAsDenovo;
      this.summaryAlleles[alleleIndex].seenInAffected =
        this.summaryAlleles[alleleIndex].seenInAffected || summaryAllele.seenInAffected;
      this.summaryAlleles[alleleIndex].seenInUnaffected =
        this.summaryAlleles[alleleIndex].seenInUnaffected || summaryAllele.seenInUnaffected;
    } else {
      this.summaryAlleles.push(summaryAllele);
      this.summaryAlleleIds.push(summaryAllele.sauid);
    }
  }

  get totalFamilyVariantsCount(): number {
    return this.summaryAlleles.reduce((a, b) => a + b.numberOfFamilyVariants, 0);
  }

  get totalSummaryAllelesCount(): number {
    return this.summaryAlleles.length;
  }
}
