import {
  UsersState
} from '../users/users-store';
import { Component, OnInit } from '@angular/core';
import { DatasetsService } from './datasets.service';
import { Dataset, DatasetsState } from './datasets';

import { IdName } from '../common/idname';
import { Store } from '@ngrx/store';
import { Observable } from 'rxjs';


@Component({
  selector: 'gpf-datasets',
  templateUrl: './datasets.component.html',
  styleUrls: ['./datasets.component.css']
})
export class DatasetsComponent implements OnInit {
  private registerAlertVisible = false;
  datasets: Dataset[];
  selectedDataset: Dataset;

  usersState: Observable<UsersState>;

  constructor(
    private store: Store<any>,
    private datasetsService: DatasetsService,
  ) {
    this.usersState = this.store.select('users');
  }

  ngOnInit() {
    this.usersState.subscribe(
      state => {
        this.datasetsService.getDatasets().subscribe(
          (datasets) => {

            this.datasets = datasets;
            this.selectDataset(0);
          });
      }
    );
  }

  selectDataset(index: number): void {
    if (index >= 0 && index < this.datasets.length) {
      if (this.datasets[index].accessRights) {
        this.selectedDataset = this.datasets[index];
        this.datasetsService.setSelectedDataset(this.selectedDataset);
        this.registerAlertVisible = false;
      }
      else {
        this.registerAlertVisible = true;
      }
    }
  }
}
