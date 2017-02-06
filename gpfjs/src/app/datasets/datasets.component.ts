import { Component, OnInit } from '@angular/core';
import { DatasetsService } from './datasets.service';
import { Dataset, DatasetsState } from './datasets';

import { IdName } from '../common/idname';


@Component({
  selector: 'gpf-datasets',
  templateUrl: './datasets.component.html',
  styleUrls: ['./datasets.component.css']
})
export class DatasetsComponent implements OnInit {

  datasets: Dataset[];
  selectedDataset: Dataset;

  constructor(
    private datasetsService: DatasetsService,
  ) {
  }

  ngOnInit() {
    this.datasetsService.getDatasets().subscribe(
      (datasets) => {

        this.datasets = datasets;
        this.selectDataset(0);
      });
  }

  selectDataset(index: number): void {
    if (index >= 0 && index < this.datasets.length) {
      this.selectedDataset = this.datasets[index];
      this.datasetsService.setSelectedDataset(this.selectedDataset);
    }
  }
}
