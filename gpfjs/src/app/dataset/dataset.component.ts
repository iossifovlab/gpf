import { Component, OnInit } from '@angular/core';
import { DatasetService } from './dataset.service';
import { Dataset } from './dataset';

import { IdName } from '../common/idname';

@Component({
  selector: 'gpf-dataset',
  templateUrl: './dataset.component.html',
  styleUrls: ['./dataset.component.css']
})
export class DatasetComponent implements OnInit {

  datasets: Dataset[];
  selectedDataset: Dataset;

  constructor(private datasetService: DatasetService) {

  }

  ngOnInit() {
    this.datasetService.getDatasets().subscribe(
      (datasets) => {
        this.datasets = datasets;
        this.selectedDataset = datasets[0];
        console.log(this.selectedDataset);
      });
  }

  selectDataset(index: number): void {
    if (index >= 0 && index < this.datasets.length) {
      this.selectedDataset = this.datasets[index];
    }
  }
}
