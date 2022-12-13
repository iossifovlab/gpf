import { Component, Input } from '@angular/core';
import { DatasetPermissions } from 'app/datasets-table/datasets-table';
import { DatasetsService } from 'app/datasets/datasets.service';
import { Item } from 'app/item-add-menu/item-add-menu';
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

  public addUser(group: UserGroup, userEvent: Item): void {
    this.usersGroupsService.addUser(userEvent.name, group.name).subscribe(() => {
      group.users.push(userEvent.name);
    });
  }

  public removeDataset(group: UserGroup, datasetId: string): void {
    // this.usersGroupsService.revokePermissionToDataset(group.name, datasetId).subscribe(() => {
    //   group.datasets = group.datasets.filter(dataset => dataset.datasetId !== datasetId);
    // });
  }

  public addDataset(group: UserGroup, datasetEvent: Item): void {
    this.usersGroupsService.grantPermissionToDataset(group.name, datasetEvent.id).subscribe(() => {
      group.datasets.push({
        datasetName: datasetEvent.name,
        datasetId: datasetEvent.id
      });
    });
  }

  public getUserNamesFunction(group: UserGroup): (page: number, searchText: string) => Observable<Item[]> {
    return (page: number, searchText: string): Observable<Item[]> =>
      this.usersService.getUsers(page, searchText).pipe(
        map((users: User[]) => users
          .filter(user => !group.users.includes(user.email))
          .map(user => new Item(user.id.toString(), user.email))
        ));
  }

  public getDatasetNamesFunction(group: UserGroup): (page: number, searchText: string) => Observable<Item[]> {
    return (page: number, searchText: string): Observable<Item[]> =>
      this.datasetsService.getManagementDatasets(page, searchText).pipe(
        map((datasets: DatasetPermissions[]) => datasets
          .filter(dataset => !group.datasets.find(d => d.datasetName === dataset.name))
          .map(dataset => new Item(dataset.id, dataset.name))
        ));
  }
}
