import { Component, OnInit, OnDestroy, ViewChild, ElementRef } from '@angular/core';
import { ActivatedRoute, NavigationStart, Router } from '@angular/router';
import { Location } from '@angular/common';
import { GeneService } from 'app/gene-browser/gene.service';
import { Gene } from 'app/gene-browser/gene';
import { SummaryAllelesArray, SummaryAllelesFilter } from 'app/gene-browser/summary-variants';
import { GenotypePreviewVariantsArray } from 'app/genotype-preview-model/genotype-preview';
import { QueryService } from 'app/query/query.service';
import { first, debounceTime, distinctUntilChanged, take, takeUntil, filter, switchMap } from 'rxjs/operators';
import { Subject, Subscription } from 'rxjs';
import { Dataset, GeneBrowser, PersonSet } from 'app/datasets/datasets';
import { FullscreenLoadingService } from 'app/fullscreen-loading/fullscreen-loading.service';
import { ConfigService } from 'app/config/config.service';
import * as d3 from 'd3';
import * as draw from 'app/utils/svg-drawing';
import { LGDS, CNV, OTHER, CODING } from 'app/effect-types/effect-types';
import { DatasetsTreeService } from 'app/datasets/datasets-tree.service';
import { MatAutocompleteTrigger } from '@angular/material/autocomplete';
import { Store } from '@ngrx/store';
import { selectDatasetId } from 'app/datasets/datasets.state';
import { DatasetsService } from 'app/datasets/datasets.service';

@Component({
  selector: 'gpf-gene-browser',
  templateUrl: './gene-browser.component.html',
  styleUrls: ['./gene-browser.component.css'],
})
export class GeneBrowserComponent implements OnInit, OnDestroy {
  @ViewChild('searchBox') private searchBox: ElementRef;
  @ViewChild('geneBrowserSearchTrigger') private geneBrowserSearchTrigger: MatAutocompleteTrigger;
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
  public familyVariantsLoaded = false;
  public geneBrowserConfig: GeneBrowser;

  public readonly affectedStatusValues = ['Affected only', 'Unaffected only', 'Affected and unaffected'];
  public readonly effectTypeValues = ['LGDs', 'missense', 'synonymous', 'CNV+', 'CNV-', 'Other'];
  public readonly variantTypeValues = ['sub', 'ins', 'del', 'CNV+', 'CNV-', 'comp'];

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
    private loadingService: FullscreenLoadingService,
    private router: Router,
    private datasetsTreeService: DatasetsTreeService,
    private store: Store,
    private datasetsService: DatasetsService
  ) {
  }

  public variantsCountDisplay: string;
  public familyVariantsCount: string;

  public ngOnInit(): void {
    this.store.select(selectDatasetId).pipe(
      take(1),
      switchMap(selectedDatasetIdState => this.datasetsService.getDataset(selectedDatasetIdState))
    ).subscribe(dataset => {
      if (!dataset) {
        return;
      }
      this.selectedDataset = dataset;
      this.selectedDatasetId = dataset.id;

      if (this.selectedDataset.accessRights) {
        this.legend = this.selectedDataset.personSetCollections.getLegend(
          this.selectedDataset.defaultPersonSetCollection
        );
      }

      this.geneBrowserConfig = this.selectedDataset.geneBrowser;
      if (this.route.snapshot.params.gene && typeof this.route.snapshot.params.gene === 'string') {
        this.geneSymbol = this.route.snapshot.params.gene;
      }

      this.enableUniqueFamilyVarinats();
    });

    this.route.queryParams.subscribe(params => {
      if (params['coding_only'] !== undefined && params['coding_only'] !== null) {
        this.summaryVariantsFilter.codingOnly = params['coding_only'] === 'true';
      }
    });

    this.subscriptions.push(
      this.queryService.streamingStartSubject.subscribe(() => {
        this.familyVariantsLoaded = false;
        this.variantsCountDisplay = 'Loading variants...';
      }),
      this.queryService.streamingFinishedSubject.subscribe(() => {
        this.familyVariantsLoaded = true;
        const count = this.genotypePreviewVariantsArray?.genotypePreviews.length;
        if (count <= this.maxFamilyVariants) {
          this.familyVariantsCount = `${count}`;
        }
      }),
      this.variantUpdate$.pipe(debounceTime(750)).subscribe(() => {
        this.updateShownTablePreviewVariantsArray();
      }),
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
  }

  private async enableUniqueFamilyVarinats(): Promise<void> {
    const childLeaves = await this.datasetsTreeService.getUniqueLeafNodes(this.selectedDatasetId);
    if (childLeaves.size > 1) {
      this.isUniqueFamilyFilterEnabled = true;
    }
  }

  public ngOnDestroy(): void {
    this.loadingService.setLoadingStop();
    this.subscriptions.map(subscription => subscription.unsubscribe());
  }

  public selectGeneSymbol(geneSymbol: string): void {
    (this.searchBox.nativeElement as HTMLElement).blur();
    this.geneSymbol = geneSymbol;
  }

  public reset(): void {
    if (!this.showResults) {
      return;
    }

    this.queryService.cancelStreamPost();
    this.geneSymbol = '';
    this.showResults = false;
    this.geneSymbolSuggestions = [];
    this.location.replaceState(`datasets/${this.selectedDatasetId}/gene-browser`);
  }

  public toggleCodingOnly($event): void {
    $event.preventDefault();
    this.showResults = false;
    this.summaryVariantsFilter.codingOnly = !this.summaryVariantsFilter.codingOnly;
  }

  public async submitGeneRequest(geneSymbol?: string): Promise<void> {
    this.showError = false;

    if (geneSymbol) {
      this.geneSymbol = geneSymbol.trim();
    }

    if (!this.geneSymbol) {
      return;
    }

    try {
      this.selectedGene = await this.geneService.getGene(
        this.geneSymbol.trim()
      ).pipe(first()).toPromise();
      this.geneSymbol = this.selectedGene.geneSymbol;
    } catch (error) {
      console.error(error);
      this.showError = true;
      this.geneBrowserSearchTrigger.closePanel();
      return;
    }
    this.showError = false;
    (this.searchBox?.nativeElement as HTMLElement)?.blur();

    this.location.replaceState(
      `datasets/${this.selectedDatasetId}/gene-browser/${this.geneSymbol}`
      + `?coding_only=${String(this.summaryVariantsFilter.codingOnly)}`
    );

    this.showResults = false;
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
    /* eslint-disable @typescript-eslint/no-unsafe-member-access */
    target.queryData.value = JSON.stringify({...this.requestParams, download: true});
    target.submit();
    /* eslint-enable */
  }

  public onSubmitSummary(): void {
    const target = document.getElementById('download-summary-form') as HTMLFormElement;
    /* eslint-disable @typescript-eslint/no-unsafe-member-access */
    target.queryData.value = JSON.stringify({...this.requestParams, download: true});
    target.submit();
    /* eslint-enable */
  }

  public updateVariants(): void {
    this.summaryVariantsArrayFiltered = this.summaryVariantsFilter.filterSummaryVariantsArray(
      this.summaryVariantsArray
    );
    const count = this.summaryVariantsArrayFiltered?.totalFamilyVariantsCount;
    this.familyVariantsCount = count > 0 && count < this.maxFamilyVariants ? `~${count}` : `${count}`;
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
    this.summaryVariantsFilter.selectedRegion = region;
    this.updateVariants();
  }

  public setSelectedFrequencies(frequencies: [number, number]): void {
    this.summaryVariantsFilter.selectedFrequencies = frequencies;
    this.updateVariants();
  }

  public getAffectedStatusColor(affectedStatus: string): string {
    return draw.affectedStatusColors[affectedStatus];
  }

  private get requestParams(): Record<string, unknown> {
    const summaryVariantsIdsToSend =
    this.summaryVariantsArrayFiltered.summaryAlleleIds.length < this.maxFamilyVariants ?
      this.summaryVariantsArrayFiltered.summaryAlleleIds : null;
    return {
      ...this.summaryVariantsFilter.queryParams,
      geneSymbols: [this.selectedGene.geneSymbol],
      datasetId: this.selectedDatasetId,
      regions: this.selectedGene.getRegionString(...this.summaryVariantsFilter.selectedRegion),
      summaryVariantIds: summaryVariantsIdsToSend,
      frequencyScores: [{
        score: this.geneBrowserConfig.frequencyColumn,
        rangeStart: this.summaryVariantsFilter.minFreq,
        rangeEnd: this.summaryVariantsFilter.maxFreq,
      }],
    };
  }

  private get requestParamsSummary(): Record<string, unknown> {
    const params = {
      datasetId: this.selectedDatasetId,
      geneSymbols: [this.geneSymbol.trim()],
      maxVariantsCount: 100000,
      inheritanceTypeFilter: ['denovo', 'mendelian', 'omission', 'missing'],
    };
    if (this.summaryVariantsFilter.codingOnly) {
      params['effectTypes'] = [...LGDS, ...CODING, ...CNV, 'CDS'];
    }
    return params;
  }

  private updateShownTablePreviewVariantsArray(): void {
    if (!this.selectedDataset.accessRights) {
      return;
    }

    const params = {
      ...this.requestParams,
      maxVariantsCount: this.maxFamilyVariants,
      uniqueFamilyVariants: this.uniqueFamilyVariants,
    };
    this.genotypePreviewVariantsArray = this.queryService.getGenotypePreviewVariantsByFilter(
      this.selectedDataset, params, this.maxFamilyVariants + 1, () => {
        this.variantsCountDisplay =
          this.genotypePreviewVariantsArray?.getVariantsCountFormatted(this.maxFamilyVariants);
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
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    let svgElement: d3.Selection<HTMLElement, undefined, HTMLElement, any>;
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
