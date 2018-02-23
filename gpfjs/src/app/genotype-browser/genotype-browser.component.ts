import { Component, Input, OnInit, OnChanges, AfterViewInit, SimpleChanges, ChangeDetectionStrategy } from '@angular/core';
import { ActivatedRoute, Params, Router } from '@angular/router';

import { Observable } from 'rxjs';
import 'rxjs/add/operator/zip';

import { QueryStateCollector } from '../query/query-state-provider';
import { QueryService } from '../query/query.service';
import { FullscreenLoadingService } from '../fullscreen-loading/fullscreen-loading.service';
import { ConfigService } from '../config/config.service';
import { StateRestoreService } from '../store/state-restore.service';
import { DatasetsService } from '../datasets/datasets.service';
import { Dataset } from '../datasets/datasets';

@Component({
  selector: 'gpf-genotype-browser',
  templateUrl: './genotype-browser.component.html',
  styleUrls: ['./genotype-browser.component.css'],
  providers: [{provide: QueryStateCollector, useExisting: GenotypeBrowserComponent}]
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
    private route: ActivatedRoute,
    private router: Router,
    private stateRestoreService: StateRestoreService,
    private datasetsService: DatasetsService,
  ) {
    super();
  }

  getCurrentState() {
    let state = this.collectState();

    return Observable.zip(...state)
      .map(state => {
        let stateObject = Object.assign(
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
