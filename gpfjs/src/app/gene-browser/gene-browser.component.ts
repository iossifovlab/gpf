import { AfterViewInit, Component, HostListener, OnInit, ViewChild } from '@angular/core';
import { GeneService } from 'app/gene-view/gene.service';
import { Gene, GeneViewSummaryAllelesArray, DomainRange } from 'app/gene-view/gene';
import { GenotypePreviewVariantsArray } from 'app/genotype-preview-model/genotype-preview';
import { QueryService } from 'app/query/query.service';
// tslint:disable-next-line:import-blacklist
import { Observable, of, combineLatest } from 'rxjs';
import { switchMap } from 'rxjs/operators';
import { Dataset } from 'app/datasets/datasets';
import { DatasetsService } from 'app/datasets/datasets.service';
import { ActivatedRoute, Params } from '@angular/router';
import { FullscreenLoadingService } from 'app/fullscreen-loading/fullscreen-loading.service';
import { GeneViewComponent } from 'app/gene-view/gene-view.component';
import { ConfigService } from 'app/config/config.service';
import { Store } from '@ngxs/store';

@Component({
  selector: 'gpf-gene-browser',
  templateUrl: './gene-browser.component.html',
  styleUrls: ['./gene-browser.component.css'],
})
export class GeneBrowserComponent implements OnInit, AfterViewInit {
  @ViewChild(GeneViewComponent) geneViewComponent: GeneViewComponent;
  selectedGene: Gene;
  geneSymbol = '';
  maxFamilyVariants = 1000;
  genotypePreviewVariantsArray: GenotypePreviewVariantsArray;
  summaryVariantsArray: GeneViewSummaryAllelesArray;
  selectedDataset$: Observable<Dataset>;
  selectedDatasetId: string;
  loadingFinished: boolean;
  familyLoadingFinished: boolean;
  hideResults: boolean;
  hideDropdown: boolean;
  showError = false;

  codingEffectTypes = [
    'lgds',
    'nonsense',
    'frame-shift',
    'splice-site',
    'no-frame-shift-newStop',
    'missense',
    'synonymous',
    'noStart',
    'noEnd',
    'no-frame-shift',
    'CDS',
    'CNV+',
    'CNV-'
  ];
  otherEffectTypes = [
    'noStart',
    'noEnd',
    'no-frame-shift',
    'non-coding',
    'intron',
    'intergenic',
    '3\'UTR',
    '3\'UTR-intron',
    '5\'UTR',
    '5\'UTR-intron',
    'CDS',
    'CNV+',
    'CNV-'
  ];
  private geneBrowserConfig;

  enableCodingOnly = true;

  @HostListener('document:keydown.enter', ['$event'])
  onEnterPress($event) {
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
  ) { }

  ngOnInit() {
    this.selectedDataset$ = this.datasetsService.getSelectedDataset();
    this.datasetsService.getSelectedDataset().subscribe(dataset => {
      this.geneBrowserConfig = dataset.geneBrowser;
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
    })
  }

  ngAfterViewInit(): void {
    this.datasetsService.getDataset(this.selectedDatasetId).subscribe(dataset => {
      if (dataset.accessRights && this.route.snapshot.params.gene) {
        this.waitForGeneViewComponent().then(() => {
          this.submitGeneRequest([this.route.snapshot.params.gene]);
        });
      }
    });
  }

  async waitForGeneViewComponent() {
    return new Promise<void>(resolve => {
      const timer = setInterval(() => {
        if (this.geneViewComponent !== undefined && this.geneViewComponent.svgElement) {
          resolve();
          clearInterval(timer);
        }
      }, 100);
    });
  }

  get state() {
    return {
      datasetId: this.selectedDatasetId,
      ...this.geneViewComponent.getState()
    }
  }

  updateShownTablePreviewVariantsArray($event: DomainRange) {
    this.familyLoadingFinished = false;
    const requestParams = this.transformFamilyVariantsQueryParameters(this.state);
    requestParams['maxVariantsCount'] = this.maxFamilyVariants;
    requestParams['summaryVariantIds'] = this.state['summaryVariantIds'];
    requestParams['uniqueFamilyVariants'] = false;
    requestParams['genomicScores'] = [{
      'metric': this.geneBrowserConfig.frequencyColumn,
      'rangeStart': $event.start > 0 ? $event.start : null,
      'rangeEnd': $event.end,
    }];
    this.selectedDataset$.subscribe( selectedDataset => {
      this.genotypePreviewVariantsArray = this.queryService.getGenotypePreviewVariantsByFilter(
        requestParams, selectedDataset.genotypeBrowserConfig.columnIds
      );
    });
  }

  transformFamilyVariantsQueryParameters(state) {
    const inheritanceFilters = [];
    if (state.showDenovo && state.showTransmitted) {
      inheritanceFilters.push('denovo');
      inheritanceFilters.push('mendelian');
      inheritanceFilters.push('omission');
      inheritanceFilters.push('missing');
    } else if (state.showDenovo) {
      inheritanceFilters.push('denovo');
    } else if (state.showTransmitted) {
      inheritanceFilters.push('mendelian');
      inheritanceFilters.push('omission');
      inheritanceFilters.push('missing');
      // inheritanceFilters.push('unknown');
    }
    let effects: string[] = state.selectedEffectTypes;
    if (effects.indexOf('other') >= 0) {
      effects = effects.filter(ef => ef !== 'other');
      effects = effects.concat(this.otherEffectTypes);
      if (this.enableCodingOnly) {
        effects = effects.filter(et => this.codingEffectTypes.indexOf(et) >= 0);
      }
    }
    const affectedStatus = new Set(state.affectedStatus);
    if (affectedStatus.has('Affected and unaffected')) {
      affectedStatus.add('Affected only');
      affectedStatus.add('Unaffected only');
    }

    const params: any = {
      'effectTypes': effects,
      'genomicScores': state.genomicScores,
      'inheritanceTypeFilter': inheritanceFilters,
      'affectedStatus': Array.from(affectedStatus.values()),
      'variantType': state.selectedVariantTypes,
      'geneSymbols': state.geneSymbols,
      'datasetId': state.datasetId
    };
    if (state.zoomState) {
      params.regions = state.regions;
    }
    return params;
  }

  startLoadingSpinner(): void {
    this.familyLoadingFinished = false;
  }

  async submitGeneRequest(geneSymbols?: string[]) {
    this.showError = false;
    this.hideDropdown = true;

    this.queryService.summaryStreamingFinishedSubject.subscribe(_ => {
      this.loadingFinished = true;
      this.loadingService.setLoadingStop();
    });

    this.queryService.streamingFinishedSubject.subscribe(() => {
      this.familyLoadingFinished = true;
    });

    let geneObservable: Observable<Gene>;
    if (geneSymbols) {
      this.geneSymbol = geneSymbols[0];
    }
    geneObservable = this.geneService.getGene(this.geneSymbol.toUpperCase().trim());

    geneObservable.subscribe(gene => {
      if (gene === undefined) {
        return;
      }
      this.selectedGene = gene;
      this.hideResults = false;
      this.loadingFinished = false;
      this.loadingService.setLoadingStart();
    }, error => {
      console.error(error);
      this.showError = true;
      this.hideDropdown = false;
    });

    this.genotypePreviewVariantsArray = null;

    const requestParams = {
      'datasetId': this.selectedDatasetId,
      'geneSymbols': [this.geneSymbol],
      'maxVariantsCount': 10000,
    }

    if (this.enableCodingOnly) {
      requestParams['effectTypes'] = this.codingEffectTypes;
    }

    const inheritanceFilters = [
      'denovo',
      'mendelian',
      'omission',
      'missing'
    ];

    requestParams['inheritanceTypeFilter'] = inheritanceFilters;

    this.summaryVariantsArray = this.queryService.getGeneViewVariants(requestParams);
    this.hideDropdown = false;
    await this.waitForGeneViewComponent();
    if (this.enableCodingOnly) {
      this.geneViewComponent.enableIntronCondensing();
    } else {
      this.geneViewComponent.disableIntronCondensing();
    }
  }

  getFamilyVariantCounts() {
    if (this.genotypePreviewVariantsArray) {
      return this.genotypePreviewVariantsArray.getVariantsCount(this.maxFamilyVariants);
    }
    return '';
  }

  onSubmit(event) {
    this.selectedDataset$.subscribe( selectedDataset => {
      const requestParams = this.transformFamilyVariantsQueryParameters(this.state);
      requestParams['summaryVariantIds'] = this.state['summaryVariantIds'];
      requestParams['genomicScores'] = [{
        'metric': this.geneBrowserConfig.frequencyColumn,
        'rangeStart': this.state['zoomState'].yMin > 0 ? this.state['zoomState'].yMin : null,
        'rangeEnd': this.state['zoomState'].yMax,
      }];
      requestParams['download'] = true;

      const targetId = event.target.attributes.id.nodeValue;
      if (targetId === 'summary_download') {
        requestParams['querySummary'] = true;
      }

      event.target.queryData.value = JSON.stringify(requestParams);
      event.target.submit();
    }, error => {
        console.warn(error);
    });
  }
}
