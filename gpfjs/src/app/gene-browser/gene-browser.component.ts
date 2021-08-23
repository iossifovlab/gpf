import { AfterViewInit, Component, HostListener, OnInit, ViewChild } from '@angular/core';
import { ActivatedRoute, Params } from '@angular/router';
import { Store } from '@ngxs/store';
import { GeneService } from 'app/gene-view/gene.service';
import { Gene, GeneViewSummaryAllele, GeneViewSummaryAllelesArray, DomainRange } from 'app/gene-view/gene';
import { GenotypePreviewVariantsArray } from 'app/genotype-preview-model/genotype-preview';
import { QueryService } from 'app/query/query.service';
// tslint:disable-next-line:import-blacklist
import { Observable, of, combineLatest } from 'rxjs';
import { switchMap, first } from 'rxjs/operators';
import { Dataset } from 'app/datasets/datasets';
import { DatasetsService } from 'app/datasets/datasets.service';
import { FullscreenLoadingService } from 'app/fullscreen-loading/fullscreen-loading.service';
import { GenePlotComponent } from 'app/gene-plot/gene-plot.component';
import { ConfigService } from 'app/config/config.service';
import { CODING, CNV, LGDS } from 'app/effecttypes/effecttypes';

@Component({
  selector: 'gpf-gene-browser',
  templateUrl: './gene-browser.component.html',
  styleUrls: ['./gene-browser.component.css'],
})
export class GeneBrowserComponent implements OnInit, AfterViewInit {
  @ViewChild(GenePlotComponent) private genePlotComponent: GenePlotComponent;
  private selectedGene: Gene;
  private geneSymbol = '';
  private maxFamilyVariants = 1000;
  private genotypePreviewVariantsArray: GenotypePreviewVariantsArray;
  private summaryVariantsArray: GeneViewSummaryAllelesArray;
  private summaryVariantsArrayFiltered: GeneViewSummaryAllelesArray;
  public selectedDataset: Dataset;
  private selectedDatasetId: string;
  private loadingFinished: boolean;
  private familyLoadingFinished: boolean;
  private showError = false;
  private geneBrowserConfig;
  private enableCodingOnly = true;

  private showDenovo = true;
  private showTransmitted = true;
  private selectedAffectedStatus: Set<string>;
  private selectedEffectTypes: Set<string>;
  private selectedVariantTypes: Set<string>;
  private selectedFrequencies: [number, number] = [0, 0];
  private selectedRegion: [number, number] = [0, 0];
  private collapsedTranscript;

  // TODO: Use effects from effecttypes.ts
  private readonly codingEffectTypes = [
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

  @HostListener('document:keydown.enter', ['$event'])
  private onEnterPress($event) {
    if ($event.target.id === 'search-box') {
      this.submitGeneRequest();
    }
  }

  constructor(
    private store: Store,
    public queryService: QueryService,
    private geneService: GeneService,
    private datasetsService: DatasetsService,
    private route: ActivatedRoute,
    readonly configService: ConfigService,
    private loadingService: FullscreenLoadingService,
  ) {
    this.selectedAffectedStatus = new Set(this.affectedStatusValues);
    this.selectedEffectTypes = new Set(this.effectTypeValues);
    this.selectedVariantTypes = new Set(this.variantTypeValues);
  }

  public ngOnInit(): void {
    this.selectedDataset = this.datasetsService.getSelectedDataset();
    if (this.selectedDataset) {
      this.geneBrowserConfig = this.selectedDataset.geneBrowser;
    }
    this.datasetsService.getDatasetsLoadedObservable()
    .subscribe(datasetsLoaded => {
      this.selectedDataset = this.datasetsService.getSelectedDataset();
      if (this.selectedDataset) {
        this.geneBrowserConfig = this.selectedDataset.geneBrowser;
      }
    });

    this.route.parent.params.subscribe(
      (params: Params) => {
        this.selectedDatasetId = params['dataset'];
      }
    );

    this.store.select(state => state.geneSymbolsState).subscribe(state => {
      if (state.geneSymbols.length) {
        this.geneSymbol = state.geneSymbols[0];
      }
    });
  }

  public ngAfterViewInit(): void {
    this.datasetsService.getDataset(this.selectedDatasetId).subscribe(dataset => {
      if (dataset.accessRights && this.route.snapshot.params.gene) {
        this.submitGeneRequest(this.route.snapshot.params.gene);
      }
    });
  }

  private async waitForGenePlotComponent() {
    return new Promise<void>(resolve => {
      const timer = setInterval(() => {
        if (this.genePlotComponent !== undefined) {
          resolve();
          clearInterval(timer);
        }
      }, 100);
    });
  }

  private updateShownTablePreviewVariantsArray() {
    this.familyLoadingFinished = false;
    const requestParams = {
      ...this.transformFamilyVariantsQueryParameters(),
      'maxVariantsCount': this.maxFamilyVariants,
      'summaryVariantIds': this.summaryVariantsArrayFiltered.summaryAlleleIds.reduce(
        (a, b) => a.concat(b), []
      ),
      'uniqueFamilyVariants': false,
      'genomicScores': [{
        'metric': this.geneBrowserConfig.frequencyColumn,
        'rangeStart': this.selectedFrequencies[0] > 0 ? this.selectedFrequencies[0] : null,
        'rangeEnd': this.selectedFrequencies[1],
      }]
    };
    this.genotypePreviewVariantsArray = this.queryService.getGenotypePreviewVariantsByFilter(
      this.selectedDataset, requestParams
    );
  }

  private transformFamilyVariantsQueryParameters() {
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
      'geneSymbols': [this.selectedGene.gene],
      'datasetId': this.selectedDatasetId,
      'regions': this.genePlotComponent.getRegionString(...this.selectedRegion),
    };
    return params;
  }

  private async submitGeneRequest(geneSymbol?: string) {
    this.showError = false;

    this.loadingFinished = false;
    this.loadingService.setLoadingStart();
    this.genotypePreviewVariantsArray = null;

    // COLLECT GENE
    if (geneSymbol) {
      this.geneSymbol = geneSymbol;
    }
    try {
      this.selectedGene = await this.geneService.getGene(
        this.geneSymbol.toUpperCase().trim()
      ).pipe(first()).toPromise();
    } catch(error) {
      console.error(error);
      this.showError = true;
    }

    if (this.selectedGene === undefined) {
      return;
    }

    const collapsedTranscript = this.selectedGene.collapsedTranscript();
    this.selectedRegion = [collapsedTranscript.start, collapsedTranscript.stop];
    this.selectedFrequencies = [0, this.geneBrowserConfig.domainMax];

    this.queryService.summaryStreamingFinishedSubject.subscribe(async() => {
      this.loadingFinished = true;
      await this.waitForGenePlotComponent();
      this.loadingService.setLoadingStop();
      this.updateShownTablePreviewVariantsArray();
    });

    this.queryService.streamingFinishedSubject.subscribe(() => {
      this.familyLoadingFinished = true;
    });

    const requestParams = {
      'datasetId': this.selectedDatasetId,
      'geneSymbols': [this.geneSymbol],
      'maxVariantsCount': 10000,
      'inheritanceTypeFilter': [
        'denovo', 'mendelian', 'omission', 'missing'
      ],
    };
    if (this.enableCodingOnly) {
      requestParams['effectTypes'] = this.codingEffectTypes;
    }

    this.summaryVariantsArray = this.queryService.getGeneViewVariants(requestParams);
    await this.queryService.summaryStreamingFinishedSubject.pipe(first()).toPromise();
    this.summaryVariantsArrayFiltered = this.filterSummaryVariantsArray(
      this.summaryVariantsArray, ...this.selectedRegion
    );
  }

  private onSubmit(event) {
    const requestParams = {
      ...this.transformFamilyVariantsQueryParameters(),
      'summaryVariantIds': this.summaryVariantsArrayFiltered.summaryAlleleIds.reduce(
        (a, b) => a.concat(b), []
      ),
      'genomicScores': [{
        'metric': this.geneBrowserConfig.frequencyColumn,
        'rangeStart': this.selectedFrequencies[0] > 0 ? this.selectedFrequencies[0] : null,
        'rangeEnd': this.selectedFrequencies[1],
      }],
      'download': true,
    };

    const targetId = event.target.attributes.id.nodeValue;
    if (targetId === 'summary_download') {
      requestParams['querySummary'] = true;
    }

    event.target.queryData.value = JSON.stringify(requestParams);
    event.target.submit();
  }

  private filterSummaryVariantsArray(
    summaryVariantsArray: GeneViewSummaryAllelesArray, startPos: number, endPos: number
  ): GeneViewSummaryAllelesArray {
    const result = new GeneViewSummaryAllelesArray();
    for (const summaryAllele of summaryVariantsArray.summaryAlleles) {
      if (this.filterSummaryAllele(summaryAllele, startPos, endPos)) {
        result.addSummaryAllele(summaryAllele);
      }
    }
    return result;
  }

  private filterSummaryAllele(summaryAllele: GeneViewSummaryAllele, startPos: number, endPos: number) {
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

  private getVariantAffectedStatus(summaryVariant: GeneViewSummaryAllele): string {
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
    this.summaryVariantsArrayFiltered = this.filterSummaryVariantsArray(
      this.summaryVariantsArray, ...this.selectedRegion
    );
    this.updateShownTablePreviewVariantsArray();
  }

  private checkShowTransmitted(checked: boolean) {
    this.showTransmitted = checked;
    this.summaryVariantsArrayFiltered = this.filterSummaryVariantsArray(
      this.summaryVariantsArray, ...this.selectedRegion
    );
    this.updateShownTablePreviewVariantsArray();
  }

  private checkEffectType(effectType: string, checked: boolean) {
    effectType = effectType.toLowerCase();
    if (checked) {
      this.selectedEffectTypes.add(effectType);
    } else {
      this.selectedEffectTypes.delete(effectType);
    }
    this.summaryVariantsArrayFiltered = this.filterSummaryVariantsArray(
      this.summaryVariantsArray, ...this.selectedRegion
    );
    this.updateShownTablePreviewVariantsArray();
  }

  private checkVariantType(variantType: string, checked: boolean) {
    variantType = variantType.toLowerCase();
    if (checked) {
      this.selectedVariantTypes.add(variantType);
    } else {
      this.selectedVariantTypes.delete(variantType);
    }
    this.summaryVariantsArrayFiltered = this.filterSummaryVariantsArray(
      this.summaryVariantsArray, ...this.selectedRegion
    );
    this.updateShownTablePreviewVariantsArray();
  }

  private checkAffectedStatus(affectedStatus: string, checked: boolean) {
    if (checked) {
      this.selectedAffectedStatus.add(affectedStatus);
    } else {
      this.selectedAffectedStatus.delete(affectedStatus);
    }
    this.summaryVariantsArrayFiltered = this.filterSummaryVariantsArray(
      this.summaryVariantsArray, ...this.selectedRegion
    );
    this.updateShownTablePreviewVariantsArray();
  }

  private setSelectedRegion(region: [number, number]) {
    this.selectedRegion = region;
    this.summaryVariantsArrayFiltered = this.filterSummaryVariantsArray(
      this.summaryVariantsArray, ...this.selectedRegion
    );
    this.updateShownTablePreviewVariantsArray();
  }

  private setSelectedFrequencies(domain: [number, number]) {
    this.selectedFrequencies = domain;
    this.summaryVariantsArrayFiltered = this.filterSummaryVariantsArray(
      this.summaryVariantsArray, ...this.selectedRegion
    );
    this.updateShownTablePreviewVariantsArray();
  }

}
