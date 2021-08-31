import { Component, Input, Output, EventEmitter, OnChanges } from '@angular/core';
import { Gene } from 'app/gene-view/gene';
import { SummaryAllele, SummaryAllelesArray } from 'app/gene-browser/summary-variants';

@Component({
  selector: 'gpf-gene-browser-filters',
  templateUrl: './gene-browser-filters.component.html',
  styleUrls: ['./gene-browser-filters.component.css']
})
export class GeneBrowserFiltersComponent implements OnChanges {

  @Input() private summaryVariantsArray: SummaryAllelesArray;
  @Input() private selectedFrequencies: [number, number] = [0, 0];
  @Input() private selectedRegion: [number, number] = [0, 0];
  @Input() private enableCodingOnly: boolean;
  @Input() private selectedDatasetId: string;
  @Input() private selectedGene: Gene;
  @Output() public filteredVariants = new EventEmitter<SummaryAllelesArray>();

  private showDenovo = true;
  private showTransmitted = true;
  private selectedAffectedStatus: Set<string>;
  private selectedEffectTypes: Set<string>;
  private selectedVariantTypes: Set<string>;

  // TODO: Use effects from effecttypes.ts
  public readonly codingEffectTypes = [
    // LGDs
    'lgds',
    // CODING
    // ...CODING,
    'nonsense', 'frame-shift', 'splice-site', 'no-frame-shift-newStop',
    'missense', 'synonymous', 'noStart', 'noEnd', 'no-frame-shift',
    // ???
    'CDS',
    // CNV
    // ...CNV,
    'CNV+', 'CNV-'
  ];
  private readonly otherEffectTypes = [
    // ???
    'noStart', 'noEnd', 'no-frame-shift', 'non-coding', 'intron', 'intergenic',
    // ???
    '3\'UTR', '3\'UTR-intron', '5\'UTR', '5\'UTR-intron',
    // ???
    'CDS',
    // CNV
    'CNV+', 'CNV-'
  ];
  private readonly lgds = ['nonsense', 'splice-site', 'frame-shift', 'no-frame-shift-new-stop'];
  private readonly affectedStatusValues = ['Affected only', 'Unaffected only', 'Affected and unaffected'];
  private readonly effectTypeValues = ['lgds', 'missense', 'synonymous', 'cnv+', 'cnv-', 'other'];
  private readonly variantTypeValues = ['sub', 'ins', 'del', 'cnv+', 'cnv-'];

  constructor() {
    this.selectedAffectedStatus = new Set(this.affectedStatusValues);
    this.selectedEffectTypes = new Set(this.effectTypeValues);
    this.selectedVariantTypes = new Set(this.variantTypeValues);
  }

  public ngOnChanges(): void {
    if (this.summaryVariantsArray !== undefined) {
      this.filteredVariants.emit(
        this.filterSummaryVariantsArray(this.summaryVariantsArray, ...this.selectedRegion)
      );
    }
  }

  private filterSummaryAllele(summaryAllele: SummaryAllele, startPos: number, endPos: number) {
    if (
      (!this.isVariantEffectSelected(summaryAllele.effect))
      || (!this.showDenovo && summaryAllele.seenAsDenovo)
      || (!this.showTransmitted && !summaryAllele.seenAsDenovo)
      || (!this.selectedAffectedStatus.has(this.getVariantAffectedStatus(summaryAllele)))
      || (!this.isVariantTypeSelected(summaryAllele.variant))
    ) {
      return false;
    } else if (summaryAllele.frequency >= this.selectedFrequencies[0]
               && summaryAllele.frequency <= this.selectedFrequencies[1]) {
      if (summaryAllele.isCNV()
        && !(summaryAllele.position <= startPos && summaryAllele.endPosition <= startPos)
        && !(summaryAllele.position >= endPos && summaryAllele.endPosition >= endPos)
      ) {
        return true;
      } else if (summaryAllele.position >= startPos && summaryAllele.position <= endPos) {
        return true;
      }
    }
    return false;
  }

  public filterSummaryVariantsArray(
    summaryVariantsArray: SummaryAllelesArray, startPos: number, endPos: number
  ): SummaryAllelesArray {
    const result = new SummaryAllelesArray();
    for (const summaryAllele of summaryVariantsArray.summaryAlleles) {
      if (this.filterSummaryAllele(summaryAllele, startPos, endPos)) {
        result.addSummaryAllele(summaryAllele);
      }
    }
    return result;
  }

  public transformFamilyVariantsQueryParameters() {
    const inheritanceFilters = [];
    if (this.showDenovo) {
      inheritanceFilters.push('denovo');
    }
    if (this.showTransmitted) {
      inheritanceFilters.push('mendelian', 'omission', 'missing');
      // inheritanceFilters.push('unknown');
    }

    let effects: string[] = Array.from(this.selectedEffectTypes);
    if (effects.includes('other')) {
      effects = effects.filter(ef => ef !== 'other');
      effects = effects.concat(this.otherEffectTypes);
      if (this.enableCodingOnly) {
        effects = effects.filter(et => this.codingEffectTypes.indexOf(et) >= 0);
      }
    }
    const affectedStatus = new Set(this.selectedAffectedStatus);
    if (affectedStatus.has('Affected and unaffected')) {
      affectedStatus.add('Affected only');
      affectedStatus.add('Unaffected only');
    }

    const params: object = {
      'effectTypes': effects,
      'inheritanceTypeFilter': inheritanceFilters,
      'affectedStatus': Array.from(affectedStatus.values()),
      'variantType': this.selectedVariantTypes,
      'geneSymbols': [this.selectedGene.geneSymbol],
      'datasetId': this.selectedDatasetId,
    };
    return params;
  }

  private isVariantEffectSelected(variantEffect: string): boolean {
    let result = false;
    variantEffect = variantEffect.toLowerCase();

    if (this.selectedEffectTypes.has(variantEffect)) {
      result = true;
    }

    if (this.lgds.indexOf(variantEffect) !== -1) {
      if (this.selectedEffectTypes.has('lgds')) {
        result = true;
      }
    } else if (
      variantEffect !== 'missense' && variantEffect !== 'synonymous' &&
      variantEffect !== 'cnv+' && variantEffect !== 'cnv-' &&
      this.selectedEffectTypes.has('other')
    ) {
      result = true;
    }

    return result;
  }

  private getVariantAffectedStatus(summaryVariant: SummaryAllele): string {
    if (summaryVariant.seenInAffected) {
      if (summaryVariant.seenInUnaffected) {
        return 'Affected and unaffected';
      } else {
        return 'Affected only';
      }
    } else {
      return 'Unaffected only';
    }
  }

  private isVariantTypeSelected(variantType: string): boolean {
    variantType = variantType.toLowerCase();
    if (variantType.substr(0, 3) === 'cnv') {
      variantType = variantType.substr(0, 4);
    } else {
      variantType = variantType.substr(0, 3);
    }
    return this.selectedVariantTypes.has(variantType);
  }

  private checkShowDenovo(checked: boolean) {
    this.showDenovo = checked;
    this.filteredVariants.emit(
      this.filterSummaryVariantsArray(this.summaryVariantsArray, ...this.selectedRegion)
    );
  }

  private checkShowTransmitted(checked: boolean) {
    this.showTransmitted = checked;
    this.filteredVariants.emit(
      this.filterSummaryVariantsArray(this.summaryVariantsArray, ...this.selectedRegion)
    );
  }

  private checkEffectType(effectType: string, checked: boolean) {
    effectType = effectType.toLowerCase();
    if (checked) {
      this.selectedEffectTypes.add(effectType);
    } else {
      this.selectedEffectTypes.delete(effectType);
    }
    this.filteredVariants.emit(
      this.filterSummaryVariantsArray(this.summaryVariantsArray, ...this.selectedRegion)
    );
  }

  private checkVariantType(variantType: string, checked: boolean) {
    variantType = variantType.toLowerCase();
    if (checked) {
      this.selectedVariantTypes.add(variantType);
    } else {
      this.selectedVariantTypes.delete(variantType);
    }
    this.filteredVariants.emit(
      this.filterSummaryVariantsArray(this.summaryVariantsArray, ...this.selectedRegion)
    );
  }

  private checkAffectedStatus(affectedStatus: string, checked: boolean) {
    if (checked) {
      this.selectedAffectedStatus.add(affectedStatus);
    } else {
      this.selectedAffectedStatus.delete(affectedStatus);
    }
    this.filteredVariants.emit(
      this.filterSummaryVariantsArray(this.summaryVariantsArray, ...this.selectedRegion)
    );
  }

}
