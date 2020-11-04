import { Component, OnInit, ViewChild } from '@angular/core';
import { GeneService } from 'app/gene-view/gene.service';
import { Gene, GeneViewSummaryVariantsArray, DomainRange } from 'app/gene-view/gene';
import { GenotypePreviewVariantsArray, GenotypePreviewInfo } from 'app/genotype-preview-model/genotype-preview';
import { QueryService } from 'app/query/query.service';
import { Observable } from 'rxjs';
import { Dataset } from 'app/datasets/datasets';
import { DatasetsService } from 'app/datasets/datasets.service';
import { ActivatedRoute, Params } from '@angular/router';
import { QueryStateCollector } from 'app/query/query-state-provider';
import { FullscreenLoadingService } from 'app/fullscreen-loading/fullscreen-loading.service';
import { GeneViewComponent } from 'app/gene-view/gene-view.component';
import { StateRestoreService } from 'app/store/state-restore.service';
import { ConfigService } from 'app/config/config.service';

@Component({
  selector: 'gpf-gene-browser-component',
  templateUrl: './gene-browser.component.html',
  styleUrls: ['./gene-browser.component.css'],
  providers: [{
    provide: QueryStateCollector,
    useExisting: GeneBrowserComponent
  }]
})
export class GeneBrowserComponent extends QueryStateCollector implements OnInit {
  @ViewChild(GeneViewComponent) geneViewComponent: GeneViewComponent;
  selectedGene: Gene;
  geneSymbol = 'CHD8';
  maxFamilyVariants = 1000;
  genotypePreviewVariantsArray: GenotypePreviewVariantsArray;
  summaryVariantsArray: GeneViewSummaryVariantsArray;
  selectedDataset$: Observable<Dataset>;
  selectedDatasetId: string;
  genotypePreviewInfo: GenotypePreviewInfo;
  loadingFinished: boolean;
  familyLoadingFinished: boolean;
  codingEffectTypes = [
    'Nonsense', 'Frame-shift', 'Splice-site',
    'No-frame-shift-newStop', 'Missense', 'Synonymous'
  ];
  otherEffectTypes = [
    'noncoding', 'noStart', 'noEnd', 'no-frame-shift',
  ];
  private geneBrowserConfig;

  enableCodingOnly = true;
  private genotypeBrowserState: Object;

  constructor(
    public queryService: QueryService,
    private geneService: GeneService,
    private datasetsService: DatasetsService,
    private route: ActivatedRoute,
    readonly configService: ConfigService,
    private loadingService: FullscreenLoadingService,
    private stateRestoreService: StateRestoreService

  ) {
    super();
  }

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
  }

  getCurrentState() {
    const state = super.getCurrentState();
    return state.map(current_state => {
      const stateObject = Object.assign({ datasetId: this.selectedDatasetId }, current_state);
      return stateObject;
    });
  }

  updateShownTablePreviewVariantsArray($event: DomainRange) {
    this.familyLoadingFinished = false;
    this.getCurrentState().subscribe(state => {
      const requestParams = this.transformFamilyVariantsQueryParameters(state, this.selectedGene);
      requestParams['maxVariantsCount'] = this.maxFamilyVariants;
      requestParams['genomicScores'] = [{
        'metric': this.geneBrowserConfig.frequencyColumn,
        'rangeStart': $event.start > 0 ? $event.start : null,
        'rangeEnd': $event.end
      }];
      this.genotypePreviewVariantsArray =
        this.queryService.getGenotypePreviewVariantsByFilter(requestParams, this.genotypePreviewInfo);
    });
  }

  transformFamilyVariantsQueryParameters(state, gene: Gene) {
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
    }
    let effects: string[] = state.selectedEffectTypes;
    if (effects.indexOf('other') >= 0) {
      effects = effects.filter(ef => ef !== 'other');
      if (!this.enableCodingOnly) {
        effects = effects.concat(this.otherEffectTypes);
      }
    }
    const params: any = {
      'effectTypes': effects,
      'genomicScores': state.genomicScores,
      'inheritanceTypeFilter': inheritanceFilters,
      "affectedStatus": state.affectedStatus,
      'datasetId': state.datasetId
    };
    if (state.zoomState) {
      const left = state.zoomState.xDomain[0];
      const right = state.zoomState.xDomain[state.zoomState.xDomain.length - 1];
      params.regions = [`${gene.transcripts[0].chrom}:${left}-${right}`];
    }
    return params;
  }

  submitGeneRequest() {
    this.getCurrentState()
      .subscribe(state => {
        this.geneSymbol = state['geneSymbols'][0];

        this.geneService.getGene(this.geneSymbol.toUpperCase().trim()).subscribe((gene) => {
          this.selectedGene = gene;
        });

        this.genotypePreviewInfo = null;
        this.loadingFinished = false;
        this.loadingService.setLoadingStart();
        this.queryService.getGenotypePreviewInfo(
          { datasetId: this.selectedDatasetId, peopleGroup: state['peopleGroup'] }
        ).subscribe(
          (genotypePreviewInfo) => {
            this.genotypePreviewInfo = genotypePreviewInfo;
            this.genotypePreviewVariantsArray = null;

            this.genotypeBrowserState = state;
            let summaryLoadingFinished = false;

            this.queryService.summaryStreamingFinishedSubject.subscribe(
              _ => {
                summaryLoadingFinished = true;
                this.loadingFinished = true;
                this.loadingService.setLoadingStop();
              });

            this.queryService.streamingFinishedSubject.subscribe(() => { this.familyLoadingFinished = true; });

            const requestParams = { ...state };
            requestParams['maxVariantsCount'] = 10000;


            if (this.enableCodingOnly) {
              requestParams['effectTypes'] = this.codingEffectTypes;
              this.geneViewComponent.enableIntronCondensing();
            } else {
              this.geneViewComponent.disableIntronCondensing();
            }
            const inheritanceFilters = [
                'denovo',
                'mendelian',
                'omission',
                'missing'
            ];

            requestParams['inheritanceTypeFilter'] = inheritanceFilters;

            this.summaryVariantsArray = this.queryService.getGeneViewVariants(requestParams);

          }, error => {
            console.warn(error);
          }
        );
      }, error => {
        console.error(error);
      });
  }

  getFamilyVariantCounts() {
    if (this.genotypePreviewVariantsArray) {
      return this.genotypePreviewVariantsArray.getVariantsCount(this.maxFamilyVariants);
    }
    return '';
  }

  onSubmit(event) {
    this.getCurrentState()
    .subscribe(
      state => {
        console.log(state);
        const requestParams = this.transformFamilyVariantsQueryParameters(state, this.selectedGene);
        requestParams['genomicScores'] = [{
          'metric': this.geneBrowserConfig.frequencyColumn,
          'rangeStart': state['zoomState'].yMin > 0 ? state['zoomState'].yMin : null,
          'rangeEnd': state['zoomState'].yMax
        }];
        event.target.queryData.value = JSON.stringify(requestParams);
        event.target.submit();
      },
      error => null
    );
  }
}
