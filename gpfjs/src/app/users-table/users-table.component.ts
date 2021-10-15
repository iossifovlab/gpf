import { Component, OnInit, NgZone, Input, OnChanges, SimpleChanges } from '@angular/core';
import { User } from '../users/users';
import { UsersService } from '../users/users.service';
import { SelectableUser } from '../user-management/user-management';
import { take } from 'rxjs/operators';

@Component({
  selector: 'gpf-users-table',
  templateUrl: './users-table.component.html',
  styleUrls: ['./users-table.component.css']
})
export class UsersTableComponent implements OnInit, OnChanges {
  @Input() users: SelectableUser[];
  allSelected = true;
  currentUserEmail: string;

  constructor(
    private zone: NgZone,
    private usersService: UsersService,
  ) { }

  ngOnInit() {
    this.usersService.getUserInfo().pipe(take(1)).subscribe((currentUser) => {
      this.currentUserEmail = currentUser.email
    });
  }

  ngOnChanges(changes: SimpleChanges) {
    if (changes && changes['users']) {
      this.allSelected = true;
    }
  }

  isDefaultGroup(user: User, group: string) {
    return user.getDefaultGroups().indexOf(group) !== -1;
  }

  removeGroup(user: User, group: string) {
    this.usersService.removeUserGroup(user, group).pipe(take(1))
      .subscribe(() => {
        this.zone.runOutsideAngular(() => {
          window.location.reload();
        });
      });
  }

  checkUncheckAll(selected) {
    for (let user of this.users) {
      user.selected = selected;
    }
  }
}
