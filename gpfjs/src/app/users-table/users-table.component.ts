import { Component, OnInit, NgZone, Input } from '@angular/core';

import { Observable, ReplaySubject } from 'rxjs';

import { User } from '../users/users';
import { UsersService } from '../users/users.service';
import { SelectableUser } from '../user-management/user-management';

@Component({
  selector: 'gpf-users-table',
  templateUrl: './users-table.component.html',
  styleUrls: ['./users-table.component.css']
})
export class UsersTableComponent implements OnInit {

  @Input()
  users: SelectableUser[];

  constructor(
    private zone: NgZone,
    private usersService: UsersService,
  ) { }

  ngOnInit() {
  }

  isDefaultGroup(user: User, group: string) {
    return user.getDefaultGroups().indexOf(group) !== -1;
  }

  removeGroup(user: User, group: string) {
    this.usersService.removeUserGroup(user, group).take(1)
      .subscribe(() => {
        this.zone.runOutsideAngular(() => {
          window.location.reload();
        });
      });
  }

}
