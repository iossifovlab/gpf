import { Component, ElementRef, OnInit, ViewChildren } from '@angular/core';

import { combineLatest, Observable, ReplaySubject } from 'rxjs';

import { User } from '../users/users';
import { UsersService } from '../users/users.service';
import { Dataset } from '../datasets/datasets';
import { DatasetsService } from '../datasets/datasets.service';
import { DatasetTableRow } from './datasets-table';
import { UsersGroupsService } from '../users-groups/users-groups.service';
import { UserGroup } from '../users-groups/users-groups';
import { debounceTime, distinctUntilChanged, map, share, switchMap, take } from 'rxjs/operators';

@Component({
  selector: 'gpf-datasets-table',
  templateUrl: './datasets-table.component.html',
  styleUrls: ['./datasets-table.component.css']
})
export class DatasetsTableComponent implements OnInit {
  tableData$: Observable<DatasetTableRow[]>;
  groups: UserGroup[];
  private datasets$: Observable<Dataset[]>;
  private usersToShow: User[];
  private users$: Observable<User[]>;
  private datasetsRefresh$ = new ReplaySubject<boolean>(1);
  @ViewChildren('errorPopup') errorPopup: ElementRef[];
  errorDisplayStyles: Object = {};
  errorMessage: String;
  delay = ms => new Promise(res => setTimeout(res, ms));

  constructor(
    private datasetsService: DatasetsService,
    private usersService: UsersService,
    private userGroupsService: UsersGroupsService
  ) {
    this.datasets$ = this.datasetsRefresh$.pipe(
      switchMap(() => this.datasetsService.getDatasets()),
      share()
    );

    this.datasets$.pipe(take(1)).subscribe(datasets => {
      datasets.forEach(dataset => {
        this.errorDisplayStyles[dataset.id] = 'none';
      })
    });
  }

  ngOnInit() {
    this.usersToShow = [];
    this.users$ = this.usersService.searchUsersByGroup(null).pipe(
      map(user => {
        this.usersToShow.push(user);
        return this.usersToShow;
      }),
      share()
    );

    this.tableData$ = combineLatest(this.datasets$, this.users$)
      .pipe(map(([datasets, users]) => this.toDatasetTableRow(datasets, users)));

    this.userGroupsService.getAllGroups()
      .pipe(take(1))
      .subscribe(groups => {
        this.groups = groups;
      });
    this.datasetsRefresh$.next(true);
  }

  datasetComparator(leftDataset: any, rightDataset: any) {
    return leftDataset.dataset.name.localeCompare(rightDataset.dataset.name);
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
    return (this.groups || []).filter(g => groups.indexOf(g.name) === -1);
  }

  async updatePermissions(dataset, groupName) {
    const groupNames = dataset.groups.map(group => group.name);

    if (groupNames.indexOf(groupName) !== -1 || groupName === '') {
      this.errorMessage = groupName === '' ? 'Please enter a group!' : 'This group already exists!';
      this.errorPopup.find(ele => ele.nativeElement.id === dataset.id + '-warning').nativeElement.setAttribute('style', 'display: block');

      this.errorDisplayStyles[dataset.id] = 'block';
      await this.delay(3000).then(() => this.errorDisplayStyles[dataset.id] = 'none');

      return;
    }

    this.userGroupsService.grantPermission(groupName, dataset).pipe(take(1))
      .subscribe(() => {
        this.datasetsRefresh$.next(true);
      });
  }

  private search = (datasetGroups: string[], text$: Observable<string>) => {
    return text$.pipe(
      debounceTime(200),
      distinctUntilChanged(),
      map(groupName => {
        if (groupName === '') {
          return [];
        }

        return this.groups
          .map(g => g.name)
          .filter(g => datasetGroups.indexOf(g) === -1)
          .filter(g => g.toLowerCase().indexOf(groupName.toLowerCase()) !== -1)
            .slice(0, 10);
      })
    );
  }

  searchGroups = (groups: string[]) => {
    return (text$: Observable<string>) => this.search(groups, text$);
  }

  isDefaultGroup(dataset: Dataset, group: string) {
    return dataset.getDefaultGroups().indexOf(group) !== -1;
  }

  removeGroup(dataset: Dataset, groupName: string) {
    this.userGroupsService.getAllGroups().pipe(
      take(1),
      switchMap(groups => {
        this.groups = groups;
        const group = this.groups.find(g => g.name === groupName);
        if (!group) {
          return;
        }
        return this.userGroupsService.revokePermission(group, dataset).pipe(take(1));
      })).subscribe(() => this.datasetsRefresh$.next(true));
  }
}
