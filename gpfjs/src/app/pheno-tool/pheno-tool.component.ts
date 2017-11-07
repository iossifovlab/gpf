import { Component, OnInit } from '@angular/core';
import { DatasetsService } from '../datasets/datasets.service';
import { ActivatedRoute, Params, Router } from '@angular/router';
import { Dataset } from '../datasets/datasets';
import { QueryStateCollector } from '../query/query-state-provider'
import { FullscreenLoadingService } from '../fullscreen-loading/fullscreen-loading.service';
import { Observable } from 'rxjs';
import { PhenoToolService } from './pheno-tool.service'
import { PhenoToolResults } from './pheno-tool-results';
import { ConfigService } from '../config/config.service';
import { Store } from '@ngrx/store';

@Component({
  selector: 'gpf-pheno-tool',
  templateUrl: './pheno-tool.component.html',
  styleUrls: ['./pheno-tool.component.css']
})
export class PhenoToolComponent extends QueryStateCollector implements OnInit {
  selectedDatasetId: string;
  selectedDataset: Dataset;

  phenoToolResults: PhenoToolResults;
  private phenoToolState: Object;

  constructor(
    private route: ActivatedRoute,
    private datasetsService: DatasetsService,
    private loadingService: FullscreenLoadingService,
    private phenoToolService: PhenoToolService,
    readonly configService: ConfigService,
    private store: Store<any>
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
            let stateObject = Object.assign({}, ...state);
            this.phenoToolState = Object.assign({},
                                          { datasetId: this.selectedDatasetId },
                                          stateObject);
          },
          error => {
            console.warn(error);
          }
        )
      }
    )
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
        this.phenoToolService.getPhenoToolResults(queryData).subscribe(
          (phenoToolResults) => {
            this.phenoToolResults = phenoToolResults;
            this.loadingService.setLoadingStop();
          },
          error => {
            this.loadingService.setLoadingStop();
          },
          () => {
            this.loadingService.setLoadingStop();
          });

      },
      error => {
        this.loadingService.setLoadingStop();
      }
    );
  }

  onDownload(event) {
    let state = this.collectState();
    Observable.zip(...state)
    .subscribe(
      state => {
        let queryData = Object.assign({},
                                      {datasetId: this.selectedDatasetId},
                                      ...state);
        event.target.queryData.value = JSON.stringify(queryData);
        console.log(event.target)
        event.target.submit();
      },
      error => null
    )
  }

}
