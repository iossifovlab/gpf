import { Component, OnInit } from '@angular/core';

import { Observable, ReplaySubject } from 'rxjs';

import { User } from '../users/users';
import { UsersService } from '../users/users.service';


@Component({
  selector: 'gpf-user-management',
  templateUrl: './user-management.component.html',
  styleUrls: ['./user-management.component.css']
})
export class UserManagementComponent implements OnInit {

  private input$ = new ReplaySubject<string>(1);
  users$: Observable<{}>;


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
      .share();

    this.search('');
  }

  search(value: string) {
    this.input$.next(value);
  }

  getUserIds(users: User[]) {
    if (!users) {
      return '';
    }

    return users.map(u => u.id).join(',');
  }
}
