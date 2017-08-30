import { Component, OnInit } from '@angular/core';

import { Observable } from 'rxjs';

import { UsersService } from '../users/users.service';

@Component({
  selector: 'gpf-users-table',
  templateUrl: './users-table.component.html',
  styleUrls: ['./users-table.component.css']
})
export class UsersTableComponent implements OnInit {
  users$: Observable<{}>;

  constructor(private usersService: UsersService) { }

  ngOnInit() {
    this.users$ = this.usersService.getAllUsers();
  }

  getGroupNames(groups: Array<any>) {
    return groups.map(g => g.name).join(', ');
  }

}
