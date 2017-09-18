import { Component, OnInit } from '@angular/core';

import { Observable, ReplaySubject } from 'rxjs';

import { User } from '../users/users';
import { UsersService } from '../users/users.service';
import { SelectableUser } from './user-management';


@Component({
  selector: 'gpf-user-management',
  templateUrl: './user-management.component.html',
  styleUrls: ['./user-management.component.css']
})
export class UserManagementComponent implements OnInit {

  private input$ = new ReplaySubject<string>(1);
  users$: Observable<SelectableUser[]>;


  constructor(
    private usersService: UsersService
    ) { }

  ngOnInit() {

    this.users$ = this.input$
      .map(searchTerm => searchTerm.trim())
      .debounceTime(300)
      .distinctUntilChanged()
      .switchMap(searchTerm =>
        this.usersService.searchUsersByGroup(searchTerm))
      .map(users => users.map(user => new SelectableUser(user)))
      .share();

    this.search('');
  }

  selectedUsers(users: SelectableUser[]) {
    if (!users) {
      return [];
    }

    return users.filter(user => user.selected)
      .map(user => user.user);
  }

  search(value: string) {
    this.input$.next(value);
  }

  getUserIds(users: SelectableUser[]) {
    if (!users) {
      return '';
    }
    const selectedUsers = this.selectedUsers(users);

    return selectedUsers.map(u => u.id).join(',');
  }
}
