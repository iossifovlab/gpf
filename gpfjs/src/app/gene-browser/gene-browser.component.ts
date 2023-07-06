import { Component, OnInit, OnDestroy, ViewChild, ElementRef } from '@angular/core';
import { ActivatedRoute, NavigationStart, Params, Router } from '@angular/router';
import { Location } from '@angular/common';
import { GeneService } from 'app/gene-browser/gene.service';
import { Gene } from 'app/gene-browser/gene';
import { SummaryAllelesArray, SummaryAllelesFilter } from 'app/gene-browser/summary-variants';
import { GenotypePreviewVariantsArray } from 'app/genotype-preview-model/genotype-preview';
import { QueryService } from 'app/query/query.service';
import { first, debounceTime, distinctUntilChanged, take, takeUntil, filter } from 'rxjs/operators';
import { Subject, Subscription } from 'rxjs';
import { Dataset, GeneBrowser, PersonSet } from 'app/datasets/datasets';
import { DatasetsService } from 'app/datasets/datasets.service';
import { FullscreenLoadingService } from 'app/fullscreen-loading/fullscreen-loading.service';
import { ConfigService } from 'app/config/config.service';
import * as d3 from 'd3';
import * as draw from 'app/utils/svg-drawing';
import { NgbDropdown } from '@ng-bootstrap/ng-bootstrap';
import { LGDS, CNV, OTHER, CODING } from 'app/effect-types/effect-types';

@Component({
  selector: 'gpf-gene-browser',
  templateUrl: './gene-browser.component.html',
  styleUrls: ['./gene-browser.component.css'],
})
export class GeneBrowserComponent implements OnInit, OnDestroy {
  @ViewChild(NgbDropdown) private dropdown: NgbDropdown;
  @ViewChild('searchBox') private searchBox: ElementRef;
  @ViewChild('filters', { static: false }) public set filters(element: HTMLElement) {
    this.drawDenovoIcons();
    this.drawTransmittedIcons();
    this.drawEffectTypesIcons();
  }

  public selectedGene: Gene;
  public geneSymbol = '';
  public maxFamilyVariants = 1000;
  public selectedDataset: Dataset;
  public showResults: boolean;
  public showError = false;
  public familyLoadingFinished: boolean;
  public geneBrowserConfig: GeneBrowser;

  public readonly affectedStatusValues = ['Affected only', 'Unaffected only', 'Affected and unaffected'];
  public readonly effectTypeValues = ['LGDs', 'missense', 'synonymous', 'CNV+', 'CNV-', 'Other'];
  public readonly variantTypeValues = ['sub', 'ins', 'del', 'CNV+', 'CNV-'];

  public genotypePreviewVariantsArray: GenotypePreviewVariantsArray;
  public summaryVariantsArray: SummaryAllelesArray;
  public summaryVariantsArrayFiltered: SummaryAllelesArray;
  public summaryVariantsFilter: SummaryAllelesFilter = new SummaryAllelesFilter();
  public uniqueFamilyVariants = false;

  public legend: Array<PersonSet>;
  public geneSymbolSuggestions: string[] = [];
  public searchBoxInput$: Subject<string> = new Subject();
  public isUniqueFamilyFilterEnabled = false;

  private subscriptions: Subscription[] = [];
  private selectedDatasetId: string;
  private variantUpdate$: Subject<void> = new Subject();
  private interruptSummaryVariants$ = new Subject();

  public constructor(
    public readonly configService: ConfigService,
    private route: ActivatedRoute,
    private location: Location,
    private queryService: QueryService,
    private geneService: GeneService,
    private datasetsService: DatasetsService,
    private loadingService: FullscreenLoadingService,
    private router: Router
  ) {
  }

  public variantsCountDisplay: string;

  public ngOnInit(): void {
    this.selectedDataset = this.datasetsService.getSelectedDataset();
    this.legend = this.selectedDataset.personSetCollections.getLegend(this.selectedDataset.defaultPersonSetCollection);
    this.geneBrowserConfig = this.selectedDataset.geneBrowser;
    if (this.route.snapshot.params.gene && typeof this.route.snapshot.params.gene === 'string') {
      void this.submitGeneRequest(this.route.snapshot.params.gene);
    }

    this.route.queryParams.subscribe(params => {
      if (params['coding_only'] !== undefined && params['coding_only'] !== null) {
        this.summaryVariantsFilter.codingOnly = params['coding_only'] === 'true';
      }
    });

    this.subscriptions.push(
      this.queryService.streamingFinishedSubject.subscribe(() => {
        this.familyLoadingFinished = true;
      }),
      this.route.parent.params.subscribe((params: Params) => {
        this.selectedDatasetId = params['dataset'] as string;
      }),
      this.variantUpdate$.pipe(debounceTime(750)).subscribe(() => this.updateShownTablePreviewVariantsArray()),
      this.searchBoxInput$.pipe(debounceTime(100), distinctUntilChanged()).subscribe(() => {
        if (!this.geneSymbol) {
          this.geneSymbolSuggestions = [];
          return;
        }
        this.geneService
          .searchGenes(this.geneSymbol)
          .pipe(take(1))
          // eslint-disable-next-line @typescript-eslint/naming-convention
          .subscribe((response: { 'gene_symbols': string[] }) => {
            this.geneSymbolSuggestions = response.gene_symbols;
          });
      }),
      this.router.events.pipe(
        filter(event => event instanceof NavigationStart)
      ).subscribe(() => {
        this.queryService.cancelStreamPost();
        this.loadingService.setLoadingStop();
      })
    );

    this.loadingService.interruptEvent.subscribe(() => {
      this.queryService.cancelStreamPost();
      this.queryService.cancelSummaryStreamPost();
      this.loadingService.setLoadingStop();
      this.location.replaceState(`datasets/${this.selectedDatasetId}/gene-browser`);
      this.interruptSummaryVariants$.next(true);
    });

    if (this.selectedDataset.studies?.length !== 0) {
      this.isUniqueFamilyFilterEnabled = true;
    }
  }

  public ngOnDestroy(): void {
    this.loadingService.setLoadingStop();
    this.subscriptions.map(subscription => subscription.unsubscribe());
  }

  public selectGeneSymbol(geneSymbol: string): void {
    this.geneSymbol = geneSymbol;
  }

  public reset(): void {
    this.showResults = false;
    this.location.replaceState(`datasets/${this.selectedDatasetId}/gene-browser`);
  }

  public openDropdown(): void {
    if (this.dropdown && !this.dropdown.isOpen()) {
      this.dropdown.open();
    }
  }

  public closeDropdown(): void {
    if (this.dropdown && this.dropdown.isOpen()) {
      this.dropdown.close();
      (this.searchBox.nativeElement as HTMLElement).blur();
    }
  }

  public async submitGeneRequest(geneSymbol?: string): Promise<void> {
    if (this.showError) {
      return;
    }

    if (geneSymbol) {
      this.geneSymbol = geneSymbol.toUpperCase().trim();
    }
    if (!this.geneSymbol) {
      return;
    }
    this.closeDropdown();
    try {
      this.selectedGene = await this.geneService.getGene(
        this.geneSymbol.toUpperCase().trim()
      ).pipe(first()).toPromise();
    } catch (error) {
      console.error(error);
      this.showError = true;
      return;
    }

    this.location.replaceState(
      `datasets/${this.selectedDatasetId}/gene-browser/${this.geneSymbol.toUpperCase()}`
      + `?coding_only=${String(this.summaryVariantsFilter.codingOnly)}`
    );

    this.showResults = false;
    this.variantsCountDisplay = 'Loading variants...';
    this.loadingService.setLoadingStart();
    this.genotypePreviewVariantsArray = null;

    this.summaryVariantsArray = new SummaryAllelesArray();
    this.queryService.getSummaryVariants(this.requestParamsSummary).pipe(take(1),
      takeUntil(this.interruptSummaryVariants$)).subscribe(res => {
      (res as object[]).forEach(row => this.summaryVariantsArray.addSummaryRow(row));
      // reset summary variants filter, without the coding only field
      this.summaryVariantsFilter = new SummaryAllelesFilter(true, true, this.summaryVariantsFilter.codingOnly);
      this.effectTypeValues.forEach(eff => this.checkEffectType(eff, true));
      this.affectedStatusValues.forEach(status => this.checkAffectedStatus(status, true));
      this.variantTypeValues.forEach(vt => this.checkVariantType(vt, true));

      this.summaryVariantsFilter.selectedRegion = [
        this.selectedGene.collapsedTranscripts[0].start,
        this.selectedGene.collapsedTranscripts[this.selectedGene.collapsedTranscripts.length - 1].stop
      ];
      this.summaryVariantsFilter.selectedFrequencies = [
        0, this.geneBrowserConfig.domainMax
      ];
      this.loadingService.setLoadingStop();
      this.showResults = true;
      this.updateVariants();
    });
  }

  public onSubmit(event: Event): void {
    const target = event.target as HTMLFormElement;
    target.queryData.value = JSON.stringify({...this.requestParams, download: true});
    target.submit();
  }

  public onSubmitSummary(): void {
    const target = document.getElementById('download-summary-form') as HTMLFormElement;
    target.queryData.value = JSON.stringify({...this.requestParams, download: true});
    target.submit();
  }

  public updateVariants(): void {
    this.summaryVariantsArrayFiltered = this.summaryVariantsFilter.filterSummaryVariantsArray(
      this.summaryVariantsArray
    );
    this.variantUpdate$.next();
  }

  public checkAffectedStatus(affectedStatus: string, value: boolean): void {
    if (value) {
      this.summaryVariantsFilter.selectedAffectedStatus.add(affectedStatus);
    } else {
      this.summaryVariantsFilter.selectedAffectedStatus.delete(affectedStatus);
    }
  }

  public checkEffectType(effectType: string, value: boolean): void {
    let effectTypes: string[];
    if (effectType === 'LGDs') {
      effectTypes = Array.from(LGDS);
    } else if (effectType === 'Other') {
      effectTypes = Array.from(OTHER);
    } else {
      effectTypes = [effectType];
    }

    for (const et of effectTypes) {
      if (value) {
        this.summaryVariantsFilter.selectedEffectTypes.add(et);
      } else {
        this.summaryVariantsFilter.selectedEffectTypes.delete(et);
      }
    }
  }

  public checkVariantType(variantType: string, value: boolean): void {
    if (value) {
      this.summaryVariantsFilter.selectedVariantTypes.add(variantType);
    } else {
      this.summaryVariantsFilter.selectedVariantTypes.delete(variantType);
    }
  }

  public checkShowDenovo(value: boolean): void {
    this.summaryVariantsFilter.denovo = value;
  }

  public checkShowTransmitted(value: boolean): void {
    this.summaryVariantsFilter.transmitted = value;
  }

  public checkUniqueFamilyVariantsFilter(): void {
    this.uniqueFamilyVariants = !this.uniqueFamilyVariants;
    this.updateShownTablePreviewVariantsArray();
  }

  public setSelectedRegion(region: [number, number]): void {
    this.familyLoadingFinished = false;
    this.summaryVariantsFilter.selectedRegion = region;
    this.updateVariants();
  }

  public setSelectedFrequencies(frequencies: [number, number]): void {
    this.familyLoadingFinished = false;
    this.summaryVariantsFilter.selectedFrequencies = frequencies;
    this.updateVariants();
  }

  public getAffectedStatusColor(affectedStatus: string): string {
    return draw.affectedStatusColors[affectedStatus];
  }

  private get requestParams(): Record<string, unknown> {
    return {
      ...this.summaryVariantsFilter.queryParams,
      geneSymbols: [this.selectedGene.geneSymbol],
      datasetId: this.selectedDatasetId,
      regions: this.selectedGene.getRegionString(...this.summaryVariantsFilter.selectedRegion),
      summaryVariantIds: this.summaryVariantsArrayFiltered.summaryAlleleIds,
      genomicScores: [{
        metric: this.geneBrowserConfig.frequencyColumn,
        rangeStart: this.summaryVariantsFilter.minFreq,
        rangeEnd: this.summaryVariantsFilter.maxFreq,
      }],
    };
  }

  private get requestParamsSummary(): Record<string, unknown> {
    const params = {
      datasetId: this.selectedDatasetId,
      geneSymbols: [this.geneSymbol.toUpperCase().trim()],
      maxVariantsCount: 10000,
      inheritanceTypeFilter: ['denovo', 'mendelian', 'omission', 'missing'],
    };
    if (this.summaryVariantsFilter.codingOnly) {
      params['effectTypes'] = [...LGDS, ...CODING, ...CNV, 'CDS'];
    }
    return params;
  }

  private updateShownTablePreviewVariantsArray(): void {
    this.familyLoadingFinished = false;
    const params = {
      ...this.requestParams,
      maxVariantsCount: this.maxFamilyVariants,
      uniqueFamilyVariants: this.uniqueFamilyVariants,
    };
    this.genotypePreviewVariantsArray = this.queryService.getGenotypePreviewVariantsByFilter(
      this.selectedDataset, params, this.maxFamilyVariants + 1, () => {
        this.variantsCountDisplay = this.genotypePreviewVariantsArray?.getVariantsCount(this.maxFamilyVariants);
      }
    );
  }

  private drawDenovoIcons(): void {
    const svgElement = d3.select('#denovo');
    draw.surroundingRectangle(svgElement, 10, 7.5, '#000000', 'Denovo LGDs');
    draw.star(svgElement, 10, 7.5, '#000000', 'Denovo LGDs');
    draw.surroundingRectangle(svgElement, 30, 8, '#000000', 'Denovo Missense');
    draw.triangle(svgElement, 30, 8, '#000000', 'Denovo Missense');
    draw.surroundingRectangle(svgElement, 50, 8, '#000000', 'Denovo Synonymous');
    draw.circle(svgElement, 50, 8, '#000000', 'Denovo Synonymous');
    draw.surroundingRectangle(svgElement, 70, 8, '#000000', 'Denovo Other');
    draw.dot(svgElement, 70, 8, '#000000', 'Denovo Other');
    draw.surroundingRectangle(svgElement, 90, 8, '#000000', 'Denovo CNV+');
    draw.rect(svgElement, 82, 98, 5, 6, '#000000', 0.4, 'Denovo CNV+');
    draw.surroundingRectangle(svgElement, 110, 8, '#000000', 'Denovo CNV-');
    draw.rect(svgElement, 102, 118, 7.5, 1, '#000000', 0.4, 'Denovo CNV-');
  }

  private drawTransmittedIcons(): void {
    const svgElement = d3.select('#transmitted');
    draw.star(svgElement, 10, 7.5, '#000000', 'LGDs');
    draw.triangle(svgElement, 30, 8, '#000000', 'Missense');
    draw.circle(svgElement, 50, 8, '#000000', 'Synonymous');
    draw.dot(svgElement, 70, 8, '#000000', 'Other');
    draw.rect(svgElement, 82, 98, 5, 6, '#000000', 0.4, 'CNV+');
    draw.rect(svgElement, 107, 125, 7.5, 1, '#000000', 0.4, 'CNV-');
  }

  private drawEffectTypesIcons(): void {
    const effectIcons = {
      /* eslint-disable  @typescript-eslint/naming-convention */
      '#LGDs': draw.star,
      '#missense': draw.triangle,
      '#synonymous': draw.circle,
      '#Other': draw.dot
      // eslint-enable
    };
    let svgElement;
    for (const [effect, drawFunc] of Object.entries(effectIcons)) {
      svgElement = d3.select(effect);
      drawFunc(svgElement, 10, 8, '#000000', effect);
    }
    svgElement = d3.select('#CNV\\+');
    draw.rect(svgElement, 5, 20, 5, 6, '#000000', 0.4, 'CNV+');
    svgElement = d3.select('#CNV-');
    draw.rect(svgElement, 5, 20, 7.5, 1, '#000000', 0.4, 'CNV-');
  }
}
