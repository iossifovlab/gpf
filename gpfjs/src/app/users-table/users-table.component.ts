import { Component, OnInit, NgZone, Input, OnChanges, SimpleChanges } from '@angular/core';
import { User } from '../users/users';
import { UsersService } from '../users/users.service';
import { take } from 'rxjs/operators';

@Component({
  selector: 'gpf-users-table',
  templateUrl: './users-table.component.html',
  styleUrls: ['./users-table.component.css']
})
export class UsersTableComponent implements OnInit {
  @Input() users: User[];
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
}
