import { Component, OnInit } from '@angular/core';

import { Observable } from 'rxjs';

import { User } from '../users/users';
import { UsersService } from '../users/users.service';
import { Dataset } from '../datasets/datasets';
import { DatasetsService } from '../datasets/datasets.service';
import { DatasetTableRow } from './datasets-table';

@Component({
  selector: 'gpf-datasets-table',
  templateUrl: './datasets-table.component.html',
  styleUrls: ['./datasets-table.component.css']
})
export class DatasetsTableComponent implements OnInit {
  tableData$: Observable<DatasetTableRow[]>;
  private datasets$: Observable<Dataset[]>;
  private users$: Observable<User[]>;

  constructor(
    private datasetsService: DatasetsService,
    private usersService: UsersService,
  ) { }

  ngOnInit() {
    this.datasets$ = this.datasetsService.getDatasets().share();
    this.users$ = this.usersService.getAllUsers().share();

    this.tableData$ = Observable.combineLatest(this.datasets$, this.users$)
      .take(1)
      .map(([datasets, users]) => this.toDatasetTableRow(datasets, users));
  }

  toDatasetTableRow(datasets: Dataset[], users: User[]) {
    let result = new Array<DatasetTableRow>();
    let groupsToUsers = users.reduce((acc, user) => {
      for (let group of user.groups) {
        if (acc[group]) {
          acc[group].push(user.email);
        } else {
          acc[group] = [user.email];
        }
      }
      return acc;
    }, {});


    for (let dataset of datasets) {
      let datasetName = dataset.name || dataset.id;
      let groups = dataset.groups.map(group => group.name);
      let datasetUsers = users.filter(user => {
         let hasGroup = dataset.groups.find(group => {
           return (groupsToUsers[group.name] || []).indexOf(user.email) !== -1;
         });
         return !!hasGroup;
      });

      let row = new DatasetTableRow(datasetName, groups, datasetUsers);
      result.push(row);
    }

    return result;
  }

}
