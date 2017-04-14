import { Component, OnInit } from '@angular/core';
import { DatasetsService } from '../datasets/datasets.service';
import { ActivatedRoute, Params, Router } from '@angular/router';
import { Dataset } from '../datasets/datasets';
import { QueryStateCollector } from '../query/query-state-provider'
import { FullscreenLoadingService } from '../fullscreen-loading/fullscreen-loading.service';
import { Observable } from 'rxjs';
import { PhenoToolService } from './pheno-tool.service'
import { PhenoToolResults } from './pheno-tool-results';

@Component({
  selector: 'gpf-pheno-tool',
  templateUrl: './pheno-tool.component.html',
  styleUrls: ['./pheno-tool.component.css']
})
export class PhenoToolComponent extends QueryStateCollector implements OnInit {
  selectedDatasetId: string;
  selectedDataset: Dataset;

  phenoToolResults: PhenoToolResults;

  constructor(
    private route: ActivatedRoute,
    private datasetsService: DatasetsService,
    private loadingService: FullscreenLoadingService,
    private phenoToolService: PhenoToolService
  ) {
    super();
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
            console.log(this.phenoToolResults);
            this.loadingService.setLoadingStop();
          });

      },
      error => {
        console.log(error);
        this.loadingService.setLoadingStop();
      }
    )
  }

}
