import { Component, OnInit, Input } from '@angular/core';
import { User } from '../users/users';
import { UsersService } from '../users/users.service';
import { map, take } from 'rxjs/operators';
import { ItemAddEvent } from 'app/item-add-menu/item-add-menu';
import { UsersGroupsService } from 'app/users-groups/users-groups.service';
import { UserGroup } from 'app/users-groups/users-groups';
import { Observable } from 'rxjs';

@Component({
  selector: 'gpf-users-table',
  templateUrl: './users-table.component.html',
  styleUrls: ['./users-table.component.css'],
})
export class UsersTableComponent {
  @Input() public users: User[];
  @Input() public currentUserEmail: string;

  public constructor(
    private usersService: UsersService,
    private usersGroupsService: UsersGroupsService
  ) { }

  public isDefaultGroup(user: User, group: string): boolean {
    return user.getDefaultGroups().indexOf(group) !== -1;
  }

  public removeGroup(user: User, group: string): void {
    this.usersService.removeUserGroup(user, group).pipe(take(1)).subscribe((res: User) => {
      user.groups = res.groups;
      user.allowedDatasets = res.allowedDatasets;
    });
  }

  public addGroup(user: User, event$: ItemAddEvent): void {
    const userClone = user.clone();
    userClone.groups.push(event$.item);

    this.usersService.updateUser(userClone).pipe(take(1)).subscribe((res: User) => {
      user.groups = res.groups;
      user.allowedDatasets = res.allowedDatasets;
    });
  }

  public getGroupNamesFunction(user: User):  (page: number, searchText: string) => Observable<string[]> {
    return (page: number, searchText: string): Observable<string[]> =>
      this.usersGroupsService.getGroups(page, searchText).pipe(
        map((groups: UserGroup[]) => groups
          .map(group => group.name)
          .filter(group => !user.groups.includes(group)))
      );
  }
}
