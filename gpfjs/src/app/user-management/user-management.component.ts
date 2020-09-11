import { Component, OnInit } from '@angular/core';
import { Router, ActivatedRoute } from '@angular/router';

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

  input$ = new ReplaySubject<string>(1);
  users: SelectableUser[] = [];
  usersToShow$: Observable<SelectableUser[]>;


  constructor(
    private usersService: UsersService,
    private router: Router,
    private route: ActivatedRoute
    ) { }

  ngOnInit() {

    this.usersToShow$ = this.input$
      .map(searchTerm => searchTerm.trim())
      .debounceTime(300)
      .distinctUntilChanged()
      .do(searchTerm => {
        this.users = [];
        let queryParamsObject: any = {};
        if (searchTerm) {
          queryParamsObject.search =  searchTerm;
        }
        this.router.navigate(['.'], {
          relativeTo: this.route,
          replaceUrl: true,
          queryParams: queryParamsObject
        });
      })
      .switchMap(searchTerm =>
        this.usersService.searchUsersByGroup(searchTerm))
      .map(user => this.sortGroups(user))
      .map(user => {
        this.users.push(new SelectableUser(user))
        return this.users;
      })
      .share();

    this.route.queryParamMap
      .map(params => params.get('search') || '')
      .take(1)
      .subscribe(searchTerm => {
        this.search(searchTerm);
      });
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

  sortGroups(user: User) {
    if (!user || !user.groups) {
      return user;
    }
    let defaultGroups = user.groups
      .filter(group => user.getDefaultGroups().indexOf(group) !== -1);
    let otherGroups = user.groups
      .filter(group => user.getDefaultGroups().indexOf(group) === -1);

    if (defaultGroups.length === 2 && defaultGroups[0] !== 'any_user') {
      let group = defaultGroups[0];
      defaultGroups[0] = defaultGroups[1];
      defaultGroups[1] = group;
    }

    otherGroups = otherGroups
      .sort((group1, group2) => group1.localeCompare(group2));

    user.groups = defaultGroups.concat(otherGroups);
    return user;
  }
}
