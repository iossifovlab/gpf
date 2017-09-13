import { Component, OnInit, NgZone } from '@angular/core';
import { Router, ActivatedRoute } from '@angular/router';

import { Observable } from 'rxjs';

import { User } from '../users/users';
import { UsersService } from '../users/users.service';

@Component({
  selector: 'gpf-users-table',
  templateUrl: './users-table.component.html',
  styleUrls: ['./users-table.component.css']
})
export class UsersTableComponent implements OnInit {
  users$: Observable<{}>;

  constructor(
    private zone: NgZone,
    private router: Router,
    private route: ActivatedRoute,
    private usersService: UsersService
  ) { }

  ngOnInit() {
    this.users$ = this.usersService.getAllUsers();
  }

  deleteUser(user: User) {
    this.usersService.deleteUser(user).take(1)
      .subscribe(() => {
        this.zone.runOutsideAngular(() => {
          window.location.reload();
        });
      });
  }

}
