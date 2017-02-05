import { Component, OnInit } from '@angular/core';
import { DatasetService } from './dataset.service';
import { Dataset, DatasetsState } from './dataset';

import { IdName } from '../common/idname';


@Component({
  selector: 'gpf-dataset',
  templateUrl: './dataset.component.html',
  styleUrls: ['./dataset.component.css']
})
export class DatasetComponent implements OnInit {

  datasets: Dataset[];
  selectedDataset: Dataset;

  constructor(
    private datasetService: DatasetService,
  ) {
  }

  ngOnInit() {
    this.datasetService.getDatasets().subscribe(
      (datasets) => {

        this.datasets = datasets;
        this.selectDataset(0);
      });
  }

  selectDataset(index: number): void {
    if (index >= 0 && index < this.datasets.length) {
      this.selectedDataset = this.datasets[index];
      this.datasetService.setSelectedDataset(this.selectedDataset);
    }
  }
}
