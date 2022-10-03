import { Component, Input, OnInit } from '@angular/core';
import { ItemAddEvent } from 'app/item-add-menu/item-add-menu';
import { User } from 'app/users/users';

import { UserGroup } from '../users-groups/users-groups';

@Component({
  selector: 'gpf-groups-table',
  templateUrl: './groups-table.component.html',
  // Order of css styles is important (second file overwrites first when needed)
  styleUrls: ['../users-table/users-table.component.css', './groups-table.component.css']
})
export class GroupsTableComponent {
  @Input() public groups: UserGroup[];

  public removeUser(user: string, group: string): void {
    // has to remove group from user
  }

  public addUser(user: string, $event: ItemAddEvent): void {
    // has to add group to user
  }

  public isDefaultGroup(user: User, group: string): boolean {
    return user.getDefaultGroups().indexOf(group) !== -1;
  }
}
