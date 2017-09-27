import { Component } from '@angular/core';
import { QueryStateCollector } from '../query/query-state-provider'
import { Observable } from 'rxjs';
import { Store } from '@ngrx/store';
import { QueryService } from '../query/query.service';
import { FullscreenLoadingService } from '../fullscreen-loading/fullscreen-loading.service';
import { ConfigService } from '../config/config.service';
import { ActivatedRoute, Params, Router } from '@angular/router';
import { StateRestoreService } from '../store/state-restore.service'
import { DatasetsService } from '../datasets/datasets.service';
import { Dataset } from '../datasets/datasets';
import 'rxjs/add/operator/zip';

@Component({
  selector: 'gpf-genotype-browser',
  templateUrl: './genotype-browser.component.html',
  styleUrls: ['./genotype-browser.component.css']
})
export class GenotypeBrowserComponent extends QueryStateCollector {
  genotypePreviewsArray: any;

  private selectedDatasetId: string;
  private genotypeBrowserState: Object;
  selectedDataset: Dataset;

  constructor(
    private store: Store<any>,
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
    this.store.subscribe(
      (param) => {
        let state = this.collectState();
        Observable.zip(...state)
        .subscribe(
          state => {
            this.genotypePreviewsArray = null
            let stateObject = Object.assign({}, ...state);
            this.genotypeBrowserState = Object.assign({},
                                          { datasetId: this.selectedDatasetId },
                                          stateObject);;
            this.router.navigate(['.', { state: JSON.stringify(stateObject)}], { relativeTo: this.route });
          },
          error => {
            this.genotypePreviewsArray = null
            console.warn(error);
          }
        )
      }
    )

    this.route.params.take(1).subscribe(
      (params: Params) => {
        this.stateRestoreService.onParamsUpdate(params['state'])
      }
    );
  }

  ngOnInit() {
    this.route.parent.params.subscribe(
      (params: Params) => {
        this.selectedDatasetId = params['dataset'];
        this.datasetsService.getDataset(this.selectedDatasetId).subscribe(
          (dataset: Dataset) => {
            this.selectedDataset = dataset;
        })
      }
    );
  }

  submitQuery() {
    this.loadingService.setLoadingStart();
    let state = this.collectState();
    Observable.zip(...state)
    .subscribe(
      state => {
        let queryData = Object.assign({},
                                      {datasetId: this.selectedDatasetId},
                                      ...state);
        this.queryService.getGenotypePreviewByFilter(queryData).subscribe(
          (genotypePreviewsArray) => {
            this.genotypePreviewsArray = genotypePreviewsArray;
            this.loadingService.setLoadingStop();
          });
      },
      error => {
        console.warn(error);
        this.loadingService.setLoadingStop();
      }
    )
  }

  onSubmit(event) {
    let state = this.collectState();
    Observable.zip(...state)
    .subscribe(
      state => {
        let queryData = Object.assign({},
                                      {datasetId: this.selectedDatasetId},
                                      ...state);
        event.target.queryData.value = JSON.stringify(queryData);
        event.target.submit();
      },
      error => null
    )
  }
}
