import { Component, Input, OnInit, OnChanges, AfterViewInit, SimpleChanges, ChangeDetectionStrategy } from '@angular/core';

import { Observable } from 'rxjs';

import { QueryStateCollector } from '../query/query-state-provider';
import { QueryService } from '../query/query.service';
import { FullscreenLoadingService } from '../fullscreen-loading/fullscreen-loading.service';
import { ConfigService } from '../config/config.service';
import { DatasetsService } from '../datasets/datasets.service';
import { Dataset } from '../datasets/datasets';

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
  genotypePreviewsArray: any;
  tablePreview: boolean;

  @Input()
  selectedDatasetId: string;
  selectedDataset$: Observable<Dataset>;
  private genotypeBrowserState: Object;

  constructor(
    private queryService: QueryService,
    readonly configService: ConfigService,
    private loadingService: FullscreenLoadingService,
    private datasetsService: DatasetsService,
  ) {
    super();
  }

  getCurrentState() {
    const state = this.collectState();

    return Observable.zip(...state, function(...states) {
      const stateJSON = {};
      for (const st of  states) {
        for (const key in st) {
          if (key in stateJSON) {
            stateJSON[key] = {...stateJSON[key], ...st[key]};
          } else {
            stateJSON[key] = st[key];
          }
        }
      }
      return stateJSON;
    })
      .map(state => {
        const stateObject = Object.assign(
          { datasetId: this.selectedDatasetId },
          ...state);
        return stateObject;
      });
  }

  ngAfterViewInit() {
    this.detectNextStateChange(() => {
        this.getCurrentState()
        .take(1)
        .subscribe(
          state => {
            this.genotypePreviewsArray = null;
            this.genotypeBrowserState = state;
          },
          error => {
            this.genotypePreviewsArray = null;
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
    this.loadingService.setLoadingStart();
    this.getCurrentState()
      .subscribe(state => {
        this.genotypePreviewsArray = null;
        this.genotypeBrowserState = state;
        this.queryService.getGenotypePreviewByFilter(state).subscribe(
          (genotypePreviewsArray) => {
            this.genotypePreviewsArray = genotypePreviewsArray;
            this.loadingService.setLoadingStop();
          },
          error => {
            console.warn(error);
            this.loadingService.setLoadingStop();
          },
          () => {
            this.loadingService.setLoadingStop();
          });
        },
        error => {
          console.warn(error);
          this.loadingService.setLoadingStop();
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
