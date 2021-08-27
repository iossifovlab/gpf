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
import { GeneBrowserFiltersComponent } from 'app/gene-browser-filters/gene-browser-filters.component';
import { ConfigService } from 'app/config/config.service';
import { CODING, CNV, LGDS } from 'app/effecttypes/effecttypes';

@Component({
  selector: 'gpf-gene-browser',
  templateUrl: './gene-browser.component.html',
  styleUrls: ['./gene-browser.component.css'],
})
export class GeneBrowserComponent implements OnInit, AfterViewInit {
  @ViewChild(GenePlotComponent) private genePlotComponent: GenePlotComponent;
  @ViewChild(GeneBrowserFiltersComponent) private geneBrowserFiltersComponent: GeneBrowserFiltersComponent;
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

  private collapsedTranscript;
  private selectedFrequencies: [number, number] = [0, 0];
  private selectedRegion: [number, number] = [0, 0];

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
      ...this.geneBrowserFiltersComponent.transformFamilyVariantsQueryParameters(),
      'regions': this.genePlotComponent.getRegionString(...this.selectedRegion),
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

  private async submitGeneRequest(geneSymbol?: string) {
    this.showError = false;

    this.loadingFinished = false;
    this.loadingService.setLoadingStart();
    this.genotypePreviewVariantsArray = null;

    // COLLECT GENE
    if (geneSymbol) {
      this.geneSymbol = geneSymbol.toUpperCase().trim();
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
      'geneSymbols': [this.geneSymbol.toUpperCase().trim()],
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
    this.summaryVariantsArrayFiltered = this.geneBrowserFiltersComponent.filterSummaryVariantsArray(
      this.summaryVariantsArray, ...this.selectedRegion
    );
  }

  private onSubmit(event) {
    const requestParams = {
      ...this.geneBrowserFiltersComponent.transformFamilyVariantsQueryParameters(),
      'regions': this.genePlotComponent.getRegionString(...this.selectedRegion),
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

  private setSelectedRegion(region: [number, number]) {
    this.selectedRegion = region;
  }

  private setSelectedFrequencies(domain: [number, number]) {
    this.selectedFrequencies = domain;
  }
}
