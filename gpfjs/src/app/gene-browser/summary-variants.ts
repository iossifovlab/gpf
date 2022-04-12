import { CNV, CODING, LGDS, OTHER } from 'app/effect-types/effect-types';

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

  public get affectedStatus() {
    if (this.seenInAffected) {
      if (this.seenInUnaffected) {
        return 'Affected and unaffected';
      } else {
        return 'Affected only';
      }
    } else {
      return 'Unaffected only';
    }
  }

  public get variantType(): string {
    return this.variant.substr(0, this.isCNV() ? 4 : 3);
  }

  public isLGDs(): boolean {
    return LGDS.has(this.effect) || this.effect === 'lgds';
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

  public isCNVMinus(): boolean {
    return (this.effect === 'CNV-');
  }

  public isCNV(): boolean {
    return this.isCNVPlus() || this.isCNVMinus();
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

    return !(this.position > allele.endPosition || this.endPosition < allele.position);
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

export class SummaryAllelesFilter {

  constructor(
    public denovo = true,
    public transmitted = true,
    public codingOnly = true,
    public selectedAffectedStatus: Set<string> = new Set(),
    public selectedEffectTypes: Set<string> = new Set(),
    public selectedVariantTypes: Set<string> = new Set(),
    public selectedFrequencies: [number, number] = [0, 0],
    public selectedRegion: [number, number] = [0, 0],
  ) {}

  public get minFreq(): number {
    return this.selectedFrequencies[0] > 0 ? this.selectedFrequencies[0] : null;
  }

  public get maxFreq(): number {
    return this.selectedFrequencies[1];
  }

  public isEffectTypeSelected(variantEffect: string): boolean {
    if (variantEffect === 'LGDs') {
      return Array.from(LGDS).every(eff => this.selectedEffectTypes.has(eff));
    } else if (variantEffect === 'Other') {
      return Array.from(OTHER).every(eff => this.selectedEffectTypes.has(eff));
    } else {
      return this.selectedEffectTypes.has(variantEffect);
    }
  }

  private filterSummaryAllele(summaryAllele: SummaryAllele): boolean {
    const [minFreq, maxFreq] = this.selectedFrequencies;
    const [startPos, endPos] = this.selectedRegion;

    if (
      (!this.denovo && summaryAllele.seenAsDenovo)
      || (!this.transmitted && !summaryAllele.seenAsDenovo)
      || (!this.selectedAffectedStatus.has(summaryAllele.affectedStatus))
      || (!this.selectedVariantTypes.has(summaryAllele.variantType))
      || (!this.isEffectTypeSelected(summaryAllele.effect))
    ) {
      return false;
    }

    if (summaryAllele.frequency < minFreq || summaryAllele.frequency > maxFreq) {
      return false;
    }

    if (summaryAllele.isCNV()
      && !(summaryAllele.position <= startPos && summaryAllele.endPosition <= startPos)
      && !(summaryAllele.position >= endPos && summaryAllele.endPosition >= endPos)
    ) {
      return true;
    } else if (summaryAllele.position >= startPos && summaryAllele.position <= endPos) {
      return true;
    } else {
      return false;
    }
  }

  public filterSummaryVariantsArray(summaryVariantsArray: SummaryAllelesArray): SummaryAllelesArray {
    const result = new SummaryAllelesArray();
    for (const summaryAllele of summaryVariantsArray.summaryAlleles) {
      if (this.filterSummaryAllele(summaryAllele)) {
        result.addSummaryAllele(summaryAllele);
      }
    }
    return result;
  }

  public get queryParams(): object {
    const inheritanceFilters = [];
    if (this.denovo) {
      inheritanceFilters.push('denovo');
    }
    if (this.transmitted) {
      inheritanceFilters.push('mendelian', 'omission', 'missing');
    }

    let effects: string[] = Array.from(this.selectedEffectTypes);
    if (this.codingOnly) {
      effects = effects.filter(et => LGDS.has(et) || CODING.has(et) || CNV.has(et) || et === 'CDS');
    }

    const affectedStatus = new Set(this.selectedAffectedStatus);
    if (this.selectedAffectedStatus.has('Affected and unaffected')) {
      affectedStatus.add('Affected only');
      affectedStatus.add('Unaffected only');
    }

    return {
      'effectTypes': effects,
      'inheritanceTypeFilter': inheritanceFilters,
      'affectedStatus': Array.from(affectedStatus),
      'variantTypes': Array.from(this.selectedVariantTypes)
    };
  }
}
