import { Component, Input } from '@angular/core';
import { ItemAddEvent } from 'app/item-add-menu/item-add-menu';
import { UsersGroupsService } from 'app/users-groups/users-groups.service';
import { User } from 'app/users/users';
import { UsersService } from 'app/users/users.service';
import { map, mergeMap, Observable } from 'rxjs';

import { UserGroup } from '../users-groups/users-groups';

@Component({
  selector: 'gpf-groups-table',
  templateUrl: './groups-table.component.html',
  // Order of css styles is important (second file overwrites the first where needed)
  styleUrls: ['../users-table/users-table.component.css', './groups-table.component.css']
})
export class GroupsTableComponent {
  @Input() public groups: UserGroup[];
  @Input() public currentUserEmail: string;

  public constructor(
    private usersGroupsService: UsersGroupsService,
    private usersService: UsersService
  ) { }

  public removeUser(group: UserGroup, userName: string): void {
    this.usersService.getUsers(0, userName).pipe(
      mergeMap(searchResults => {
        const user = searchResults.find(u => u.name === userName);
        user.groups.push(group.name);
        return this.usersService.updateUser(user);
      })
    ).subscribe((res: User) => {
      group.users.push(res.name);
    });
  }

  public addUser(group: UserGroup, userEvent: ItemAddEvent): void {
    this.usersService.getUsers(0, userEvent.item).pipe(
      mergeMap(searchResults => {
        const user = searchResults.find(u => u.name === userEvent.item);
        return this.usersService.removeUserGroup(user, group.name);
      })
    ).subscribe((res: User) => {
      group.users.splice(group.users.indexOf(res.name, 0), 1);
    });
  }

  public removeDataset(group: UserGroup, datasetName: string): void {
    // need dataset id or use name
  }

  public addDataset(group: UserGroup, datasetEvent: ItemAddEvent): void {
    // need dataset id or use name
  }

  public getUserNamesFunction(group: UserGroup):  (page: number, searchText: string) => Observable<string[]> {
    return (page: number, searchText: string): Observable<string[]> =>
      this.usersService.getUsers(page, searchText).pipe(
        map((users: User[]) => users
          .map(user => user.email)
          .filter(user => !group.users.includes(user)))
      );
  }
}
