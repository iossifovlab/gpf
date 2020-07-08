
import {throwError as observableThrowError,  Observable, BehaviorSubject } from 'rxjs';
import { Component, OnInit } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';

import { User } from '../users/users';
import { UsersService } from '../users/users.service';
import { UserGroup } from '../users-groups/users-groups';
import { UsersGroupsService } from '../users-groups/users-groups.service';
import { IDropdownSettings } from 'ng-multiselect-dropdown';


@Component({
  selector: 'gpf-groups-bulk-remove',
  templateUrl: './groups-bulk-remove.component.html',
  styleUrls: ['./groups-bulk-remove.component.css']
})
export class GroupsBulkRemoveComponent implements OnInit {
  users$ = new BehaviorSubject<User[]>(null);
  groups$: Observable<UserGroup[]>;
  group: string;
  dropdownSettings: IDropdownSettings = {};

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private usersService: UsersService,
    private usersGroupsService: UsersGroupsService
  ) { }

  ngOnInit() {
    let parameterUsers = this.getUsersOrBack();
    parameterUsers.take(1)
      .subscribe(users => {
        this.users$.next(users);
      });
    this.groups$ = this.usersGroupsService.getAllGroups();

    this.dropdownSettings = {
      singleSelection: true,
      idField: 'id',
      textField: 'text',
      allowSearchFilter: true
    };
  }

  getUsersOrBack() {
    let parameterIds = this.route.queryParams.take(1)
      .do(params => {
        if (!params['user_ids']) {
          this.router.navigate(['..'], { relativeTo: this.route });
          return observableThrowError('No user ids..');
        }
      })
      .map(params => params['user_ids'].split(',') as string[])
      .map(ids => ids.map(id => +id.trim()));

    let allUsers = this.usersService.getAllUsers().take(1);

    return Observable.combineLatest(parameterIds, allUsers)
      .switchMap(([ids, users]: [number[], User[]]) => {
        let filteredUsers = users.filter(u => ids.indexOf(u.id) !== -1);
        if (filteredUsers.length !== ids.length) {
          this.router.navigate(['..'], { relativeTo: this.route });
          return observableThrowError('unknown ids...');
        }

        return Observable.of(filteredUsers);
      });
  }

  groupsToOptions(groups: UserGroup[]) {
    if (!groups) {
      return null;
    }
    return groups.map(group => {
      return {
        id: group.name,
        text: group.name
      };
    });
  }

  groupsToValue(groups: UserGroup[]) {
    if (!groups) {
      return [];
    }
    return groups.map(group => group.id.toString());
  }


  submit() {
    if (!this.group) {
      return;
    }
    let users = this.users$.value;
    if (!users) {
      return;
    }
    this.usersService.bulkRemoveGroup(users, this.group)
      .take(1)
      .subscribe(() => this.router.navigate(['/management']));
  }

  changeSelectedGroup(group) {
    this.group = group;
  }

}
