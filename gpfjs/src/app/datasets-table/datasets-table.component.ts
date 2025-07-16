import { Component, Input } from '@angular/core';
import { Observable } from 'rxjs';
import { DatasetsService } from '../datasets/datasets.service';
import { DatasetPermissions } from './datasets-table';
import { UsersGroupsService } from '../users-groups/users-groups.service';
import { UserGroup } from '../users-groups/users-groups';
import { map, mergeMap } from 'rxjs/operators';
import { Item } from 'app/item-add-menu/item-add-menu';

@Component({
    selector: 'gpf-datasets-table',
    templateUrl: './datasets-table.component.html',
    // Order of css files is important (second file overwrites the first where needed)
    styleUrls: ['../users-table/users-table.component.css', './datasets-table.component.css'],
    standalone: false
})
export class DatasetsTableComponent {
  @Input() public datasets: DatasetPermissions[];

  public constructor(
    private usersGroupsService: UsersGroupsService,
    private datasetsService: DatasetsService
  ) { }

  public isDefaultGroup(dataset: DatasetPermissions, group: string): boolean {
    return dataset.getDefaultGroups().indexOf(group) !== -1;
  }

  public removeGroup(dataset: DatasetPermissions, groupToRemove: string): void {
    this.usersGroupsService.getGroup(groupToRemove).pipe(
      mergeMap(group => this.usersGroupsService.revokePermissionToDataset(group.id, dataset.id)),
      mergeMap(() => this.datasetsService.getManagementDataset(dataset.id))
    ).subscribe(updatedDataset => {
      dataset.groups = updatedDataset.groups;
      dataset.users = updatedDataset.users;
    });
  }

  public addGroup(dataset: DatasetPermissions, groupEvent: Item): void {
    if (!groupEvent.name) {
      return;
    }

    this.usersGroupsService.grantPermissionToDataset(groupEvent.name, dataset.id).pipe(
      mergeMap(() => this.datasetsService.getManagementDataset(dataset.id))
    ).subscribe(updatedDataset => {
      dataset.groups = updatedDataset.groups;
      dataset.users = updatedDataset.users;
    });
  }

  public getGroupNamesFunction(dataset: DatasetPermissions): (page: number, searchText: string) => Observable<Item[]> {
    return (page: number, searchText: string): Observable<Item[]> =>
      this.usersGroupsService.getGroups(page, searchText).pipe(
        map((groups: UserGroup[]) => groups
          .filter(group => !dataset.groups.includes(group.name))
          .map(group => new Item(group.id.toString(), group.name))
        ));
  }
}
