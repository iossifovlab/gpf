import { Component, OnInit } from '@angular/core';

import { Observable, ReplaySubject } from 'rxjs';

import { User } from '../users/users';
import { UsersService } from '../users/users.service';
import { Dataset } from '../datasets/datasets';
import { DatasetsService } from '../datasets/datasets.service';
import { DatasetTableRow } from './datasets-table';
import { UsersGroupsService } from '../users-groups/users-groups.service';
import { UserGroup } from '../users-groups/users-groups';

@Component({
  selector: 'gpf-datasets-table',
  templateUrl: './datasets-table.component.html',
  styleUrls: ['./datasets-table.component.css']
})
export class DatasetsTableComponent implements OnInit {
  tableData$: Observable<DatasetTableRow[]>;
  groups: UserGroup[];
  private datasets$: Observable<Dataset[]>;
  private users$: Observable<User[]>;
  private datasetsRefresh$ = new ReplaySubject<boolean>(1);

  constructor(
    private datasetsService: DatasetsService,
    private usersService: UsersService,
    private userGroupsService: UsersGroupsService
  ) { }

  ngOnInit() {
    this.datasets$ = this.datasetsRefresh$
      .switchMap(() => this.datasetsService.getDatasets())
      .share();
    this.users$ = this.usersService.getAllUsers().share();

    this.tableData$ = Observable.combineLatest(this.datasets$, this.users$)
      .map(([datasets, users]) => this.toDatasetTableRow(datasets, users));

    this.userGroupsService.getAllGroups()
      .take(1)
      .subscribe(groups => {
        this.groups = groups;
      });
    this.datasetsRefresh$.next(true);
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
      let groups = dataset.groups.map(group => group.name);
      let datasetUsers = users.filter(user => {
         let hasGroup = dataset.groups.find(group => {
           return (groupsToUsers[group.name] || []).indexOf(user.email) !== -1;
         });
         return !!hasGroup;
      });

      let row = new DatasetTableRow(dataset, groups, datasetUsers);
      result.push(row);
    }

    return result;
  }

  alwaysSelected(groups: string[]) {
    return (this.groups || []).filter(g => groups.indexOf(g.name) === -1)
  }

  updatePermissions(dataset, groupName) {
    let group = this.groups.find(g => g.name === groupName);
    if (!group) {
      return;
    }
    this.userGroupsService.grantPermission(group, dataset)
      .take(1)
      .subscribe(() => {
        this.datasetsRefresh$.next(true);
      });
  }

  private search = (datasetGroups: string[], text$: Observable<string>) => {
    return text$
      .debounceTime(200)
      .distinctUntilChanged()
      .map(groupName => {
        if (groupName === "") {
          return [];
        }

        return this.groups
          .map(g => g.name)
          .filter(g => datasetGroups.indexOf(g) === -1)
          .filter(g => g.toLowerCase().indexOf(groupName.toLowerCase()) !== -1)
            .slice(0, 10);
      });
  }

  searchGroups = (groups: string[]) => {
    return (text$: Observable<string>) => this.search(groups, text$)
  }

  isDefaultGroup(dataset: Dataset, group: string) {
    return dataset.getDefaultGroups().indexOf(group) !== -1;
  }

  removeGroup(dataset: Dataset, groupName: string) {
    let group = this.groups.find(g => g.name === groupName);
    if (!group) {
      return;
    }
    this.userGroupsService.revokePermission(group, dataset)
      .take(1)
      .subscribe(() => {
        this.datasetsRefresh$.next(true);
      });
  }

}
