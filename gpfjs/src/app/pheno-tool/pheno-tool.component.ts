import { Component, OnInit } from '@angular/core';
import { DatasetsService } from '../datasets/datasets.service';
import { ActivatedRoute, Params, Router } from '@angular/router';
import { Dataset } from '../datasets/datasets';
import { QueryStateCollector } from '../query/query-state-provider'
import { FullscreenLoadingService } from '../fullscreen-loading/fullscreen-loading.service';
import { Observable } from 'rxjs';

@Component({
  selector: 'gpf-pheno-tool',
  templateUrl: './pheno-tool.component.html',
  styleUrls: ['./pheno-tool.component.css']
})
export class PhenoToolComponent extends QueryStateCollector implements OnInit {
  selectedDatasetId: string;
  selectedDataset: Dataset;

  constructor(
    private route: ActivatedRoute,
    private datasetsService: DatasetsService,
    private loadingService: FullscreenLoadingService,
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
    console.log(this);
    //this.loadingService.setLoadingStart();
    let state = this.collectState();

    console.log("PT ST1", state);
    Observable.zip(...state)
    .subscribe(
      state => {
        let queryData = Object.assign({},
                                      {datasetId: this.selectedDatasetId},
                                      ...state);
        console.log("PT ST2", queryData);

      },
      error => {
        console.log(error);
        this.loadingService.setLoadingStop();
      }
    )
  }

}
