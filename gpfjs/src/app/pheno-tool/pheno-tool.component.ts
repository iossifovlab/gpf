import { Component, OnInit } from '@angular/core';
import { DatasetsService } from '../datasets/datasets.service';
import { ActivatedRoute, Params, Router } from '@angular/router';
import { Dataset } from '../datasets/datasets';

@Component({
  selector: 'gpf-pheno-tool',
  templateUrl: './pheno-tool.component.html',
  styleUrls: ['./pheno-tool.component.css']
})
export class PhenoToolComponent implements OnInit {
  selectedDatasetId: string;
  selectedDataset: Dataset;

  constructor(
    private route: ActivatedRoute,
    private datasetsService: DatasetsService,

  ) { }

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

}
