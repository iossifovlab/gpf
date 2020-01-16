import { Component, Input, OnInit, OnChanges, AfterViewInit, SimpleChanges } from '@angular/core';

import { Observable } from 'rxjs';

import { QueryStateCollector } from '../query/query-state-provider';
import { QueryService } from '../query/query.service';
import { FullscreenLoadingService } from '../fullscreen-loading/fullscreen-loading.service';
import { ConfigService } from '../config/config.service';
import { DatasetsService } from '../datasets/datasets.service';
import { Dataset } from '../datasets/datasets';
import { GenotypePreviewInfo, GenotypePreviewVariantsArray } from 'app/genotype-preview-model/genotype-preview';

@Component({
  selector: 'gpf-genotype-browser',
  templateUrl: './genotype-browser.component.html',
  styleUrls: ['./genotype-browser.component.css'],
  providers: [{
    provide: QueryStateCollector,
    useExisting: GenotypeBrowserComponent
  }]
})
export class GenotypeBrowserComponent extends QueryStateCollector
    implements OnInit, OnChanges, AfterViewInit {
  genotypePreviewVariantsArray: GenotypePreviewVariantsArray;
  genotypePreviewInfo: GenotypePreviewInfo;
  tablePreview: boolean;

  @Input()
  selectedDatasetId: string;
  selectedDataset$: Observable<Dataset>;
  private genotypeBrowserState: Object;
  private loadingFinished: boolean;

  constructor(
    private queryService: QueryService,
    readonly configService: ConfigService,
    private loadingService: FullscreenLoadingService,
    private datasetsService: DatasetsService,
  ) {
    super();
  }

  getCurrentState() {
    const state = super.getCurrentState();

    return state.map(current_state => {
        const stateObject = Object.assign(
          { datasetId: this.selectedDatasetId },
          ...current_state);
        return stateObject;
      });
  }

  ngAfterViewInit() {
    this.detectNextStateChange(() => {
        this.getCurrentState()
        .take(1)
        .subscribe(
          state => {
            this.genotypePreviewVariantsArray = null;
            this.genotypeBrowserState = state;
          },
          error => {
            this.genotypePreviewVariantsArray = null;
            console.warn(error);
          });
      });
  }

  ngOnInit() {
    this.selectedDataset$ = this.datasetsService.getSelectedDataset();
  }

  ngOnChanges(changes: SimpleChanges) {
    this.datasetsService.setSelectedDatasetById(this.selectedDatasetId);
  }

  submitQuery() {
    this.getCurrentState()
      .subscribe(state => {

        this.genotypePreviewInfo = null;
        this.loadingFinished = false;
        this.loadingService.setLoadingStart();

        this.queryService.getGenotypePreviewInfo(
          { datasetId: state.datasetId, peopleGroup: state.peopleGroup }
        ).subscribe(
          (genotypePreviewInfo) => {
            this.genotypePreviewInfo = genotypePreviewInfo;
            this.genotypePreviewVariantsArray = null;

            this.genotypeBrowserState = state;

            this.queryService.streamingFinishedSubject.subscribe(
              _ => { this.loadingFinished = true; }
            );

            this.genotypePreviewVariantsArray =
              this.queryService.getGenotypePreviewVariantsByFilter(
                state, this.genotypePreviewInfo, this.loadingService
              );

          }, error => {
            console.warn(error);
          }
        );
      }, error => {
        console.warn(error);
      });
  }

  onSubmit(event) {
    this.getCurrentState()
    .subscribe(
      state => {
        event.target.queryData.value = JSON.stringify(state);
        event.target.submit();
      },
      error => null
    );
  }
}
