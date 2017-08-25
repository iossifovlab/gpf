import { Component, OnInit } from '@angular/core';

import { Observable } from 'rxjs';

import { UsersService } from '../users/users.service';

@Component({
  selector: 'gpf-users-table',
  templateUrl: './users-table.component.html',
  styleUrls: ['./users-table.component.css']
})
export class UsersTableComponent implements OnInit {

  constructor(private usersService: UsersService) { }

  private users$: Observable<{}>;

  ngOnInit() {
    this.users$ = this.usersService.getAllUsers();
  }

  getGroupNames(groups: Array<any>) {
    return groups.map(g => g.name).join(", ");
  }

}
