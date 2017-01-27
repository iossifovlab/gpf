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

  datasets: IdName[];
  selectedDataset: Dataset;

  constructor(private datasetService: DatasetService) {

  }

  ngOnInit() {
    this.datasetService.getDatasets().subscribe(
      (datasets) => {
        this.datasets = datasets;

        this.datasetService
          .getDataset(this.datasets[0].id)
          .subscribe(dataset => {
            this.selectedDataset = dataset;
            console.log('selected dataset is: ', this.selectedDataset.id);
          });
      },
      (err) => {
        alert(`Error receiving datasets: ${err}`);
      });
  }

}
