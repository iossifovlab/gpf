import { Component, Input } from '@angular/core';
import { DatasetPermissions } from 'app/datasets-table/datasets-table';
import { DatasetsService } from 'app/datasets/datasets.service';
import { ItemAddEvent } from 'app/item-add-menu/item-add-menu';
import { UsersGroupsService } from 'app/users-groups/users-groups.service';
import { User } from 'app/users/users';
import { UsersService } from 'app/users/users.service';
import { map, Observable } from 'rxjs';

import { UserGroup } from '../users-groups/users-groups';

@Component({
  selector: 'gpf-groups-table',
  templateUrl: './groups-table.component.html',
  // Order of css files is important (second file overwrites the first where needed)
  styleUrls: ['../users-table/users-table.component.css', './groups-table.component.css']
})
export class GroupsTableComponent {
  @Input() public groups: UserGroup[];
  @Input() public currentUserEmail: string;

  public constructor(
    private usersService: UsersService,
    private usersGroupsService: UsersGroupsService,
    private datasetsService: DatasetsService
  ) { }

  public removeUser(group: UserGroup, userEmail: string): void {
    this.usersGroupsService.removeUser(userEmail, group.name).subscribe(() => {
      group.users = group.users.filter(user => user !== userEmail);
    });
  }

  public addUser(group: UserGroup, userEvent: ItemAddEvent): void {
    this.usersGroupsService.addUser(userEvent.item, group.name).subscribe(() => {
      group.users.push(userEvent.item);
    });
  }

  public removeDataset(group: UserGroup, datasetId: string): void {
    this.usersGroupsService.revokePermissionToDataset(group.name, datasetId).subscribe(() => {
      group.datasets = group.datasets.filter(dataset => dataset.datasetId !== datasetId);
    });
  }

  public addDataset(group: UserGroup, datasetEvent: ItemAddEvent): void {
    // const datasetId = group.datasets.find(dataset => dataset.datasetName === datasetEvent.item).datasetId;
    // this.usersGroupsService.grantPermissionToDataset(group.name, datasetId).subscribe(() => {
    //   group.datasets.push({
    //     datasetName: datasetEvent.item,
    //     datasetId: datasetId
    //   });
    // });
  }

  public getUserNamesFunction(group: UserGroup): (page: number, searchText: string) => Observable<string[]> {
    return (page: number, searchText: string): Observable<string[]> =>
      this.usersService.getUsers(page, searchText).pipe(
        map((users: User[]) => users
          .map(user => user.email)
          .filter(user => !group.users.includes(user)))
      );
  }

  public getDatasetNamesFunction(group: UserGroup): (page: number, searchText: string) => Observable<string[]> {
    return (page: number, searchText: string): Observable<string[]> =>
      this.datasetsService.getManagementDatasets(page, searchText).pipe(
        map((datasets: DatasetPermissions[]) => datasets
          .map(dataset => dataset.name)
          .filter(datasetName => !group.datasets.find(dataset => dataset.datasetName === datasetName)))
      );
  }
}
