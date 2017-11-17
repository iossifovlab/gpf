import { Component, Input, OnChanges, AfterViewInit, SimpleChanges } from '@angular/core';
import { QueryStateCollector } from '../query/query-state-provider';
import { Observable } from 'rxjs';
import { QueryService } from '../query/query.service';
import { FullscreenLoadingService } from '../fullscreen-loading/fullscreen-loading.service';
import { ConfigService } from '../config/config.service';
import { ActivatedRoute, Params, Router } from '@angular/router';
import { StateRestoreService } from '../store/state-restore.service';
import { DatasetsService } from '../datasets/datasets.service';
import { Dataset } from '../datasets/datasets';
import 'rxjs/add/operator/zip';

@Component({
  selector: 'gpf-genotype-browser',
  templateUrl: './genotype-browser.component.html',
  styleUrls: ['./genotype-browser.component.css']
})
export class GenotypeBrowserComponent extends QueryStateCollector
    implements OnChanges, AfterViewInit {
  genotypePreviewsArray: any;
  tablePreview: boolean;

  @Input()
  selectedDatasetId: string;
  selectedDataset$: Observable<Dataset>;
  private genotypeBrowserState: Object;
  isMissenseSelected = false;

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

  ngAfterViewInit() {
    this.selectedDataset$ = this.datasetsService.getSelectedDataset();
    // FIXME: figure out when to collect the state
    // this.store.subscribe(
      // (param) => {
        let stateArray = this.collectState();
        Observable.zip(...stateArray)
        .subscribe(
          state => {
            this.genotypePreviewsArray = null;
            let stateObject = Object.assign({}, ...state);
            this.isMissenseSelected = stateObject.effectTypes.includes('Missense');
            this.genotypeBrowserState = Object.assign({},
                                          { datasetId: this.selectedDatasetId },
                                          stateObject);
            this.router.navigate(
              [ '.', { state: JSON.stringify(stateObject) }],
              { relativeTo: this.route }
            );
          },
          error => {
            this.genotypePreviewsArray = null;
            console.warn(error);
          }
        );
    //   }
    // )

    this.route.params.take(1).subscribe(
      (params: Params) => {
        this.stateRestoreService.onParamsUpdate(params['state']);
      }
    );
  }

  ngOnChanges(changes: SimpleChanges) {
    this.datasetsService.setSelectedDatasetById(this.selectedDatasetId);
  }

  submitQuery() {
    this.loadingService.setLoadingStart();
    let stateArray = this.collectState();
    Observable.zip(...stateArray)
    .subscribe(
      state => {
        let queryData = Object.assign({},
                                      {datasetId: this.selectedDatasetId},
                                      ...state);
        console.log("query data", queryData)
        this.queryService.getGenotypePreviewByFilter(queryData).subscribe(
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
      }
    );
  }

  onSubmit(event) {
    let stateArray = this.collectState();
    Observable.zip(...stateArray)
    .subscribe(
      state => {
        let queryData = Object.assign({},
                                      {datasetId: this.selectedDatasetId},
                                      ...state);
        event.target.queryData.value = JSON.stringify(queryData);
        event.target.submit();
      },
      error => null
    );
  }
}
