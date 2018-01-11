import { Component, OnInit, AfterViewInit } from '@angular/core';
import { DatasetsService } from '../datasets/datasets.service';
import { ActivatedRoute, Params, Router } from '@angular/router';
import { Dataset } from '../datasets/datasets';
import { QueryStateCollector } from '../query/query-state-provider';
import { FullscreenLoadingService } from '../fullscreen-loading/fullscreen-loading.service';
import { Observable } from 'rxjs';
import { PhenoToolService } from './pheno-tool.service';
import { PhenoToolResults } from './pheno-tool-results';
import { ConfigService } from '../config/config.service';

@Component({
  selector: 'gpf-pheno-tool',

  templateUrl: './pheno-tool.component.html',
  styleUrls: ['./pheno-tool.component.css']
})
export class PhenoToolComponent extends QueryStateCollector
    implements OnInit, AfterViewInit {
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
  ) {
    super();
  }

  ngAfterViewInit() {
    this.detectNextStateChange(() => {
      let stateArray = this.collectState();
      Observable.zip(...stateArray)
        .subscribe(state => {
          let stateObject = Object.assign({}, ...state);
          this.phenoToolState = Object.assign(
            {},
            { datasetId: this.selectedDatasetId },
            stateObject);
        },
        error => {
          console.warn(error);
        });
    });
  }

  ngOnInit() {
    this.datasetsService.getSelectedDataset()
      .subscribe(dataset => {
        this.selectedDatasetId = dataset.id;
        this.selectedDataset = dataset;
      });
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
    let stateArray = this.collectState();
    Observable.zip(...stateArray)
      .subscribe(state => {
        let queryData = Object.assign({},
                                      {datasetId: this.selectedDatasetId},
                                      ...state);
        event.target.queryData.value = JSON.stringify(queryData);
        console.log(event.target);
        event.target.submit();
      },
      error => null
    );
  }

}
