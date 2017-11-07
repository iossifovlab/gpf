import { Component, OnInit, NgZone, Input } from '@angular/core';
import { Router, ActivatedRoute } from '@angular/router';

import { User } from '../users/users';
import { UsersService } from '../users/users.service';

@Component({
  selector: 'gpf-users-actions',
  templateUrl: './users-actions.component.html',
  styleUrls: ['./users-actions.component.css']
})
export class UsersActionsComponent implements OnInit {
  @Input()
  user: User;

  constructor(
    private zone: NgZone,
    private router: Router,
    private route: ActivatedRoute,
    private usersService: UsersService
  ) { }

  ngOnInit() {
  }

  deleteUser(user: User) {
    this.usersService.deleteUser(user).take(1)
      .subscribe(() => {
        this.reloadPage();
      });
  }

  removePassword(user: User) {
    this.usersService.removeUserPassword(user).take(1)
      .subscribe(() => {
        this.reloadPage();
      });
  }
  resetPassword(user: User) {
    this.usersService.resetUserPassword(user).take(1)
      .subscribe(() => {
        this.reloadPage();
      });
  }

  reloadPage() {
    this.zone.runOutsideAngular(() => {
      window.location.reload();
    });
  }

}
