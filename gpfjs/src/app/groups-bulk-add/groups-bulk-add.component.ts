
import {throwError as observableThrowError,  Observable, BehaviorSubject, combineLatest, of } from 'rxjs';
import { Component, OnInit, ViewChild } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';

import { User } from '../users/users';
import { UsersService } from '../users/users.service';
import { UserGroup } from '../users-groups/users-groups';
import { UsersGroupsService } from '../users-groups/users-groups.service';
import { UserGroupsSelectorComponent } from 'app/user-groups-selector/user-groups-selector.component';
import { map, switchMap, take, tap } from 'rxjs/operators';

@Component({
  selector: 'gpf-groups-bulk-add',
  templateUrl: './groups-bulk-add.component.html',
  styleUrls: ['./groups-bulk-add.component.css']
})
export class GroupsBulkAddComponent implements OnInit {
  users$ = new BehaviorSubject<User[]>(null);
  groups$: Observable<UserGroup[]>;

  @ViewChild(UserGroupsSelectorComponent)
  private userGroupsSelectorComponent: UserGroupsSelectorComponent;

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private usersService: UsersService,
    private usersGroupsService: UsersGroupsService
  ) { }

  ngOnInit() {
    const parameterUsers = this.getUsersOrBack();

    parameterUsers.pipe(take(1)).subscribe(users => {
      this.users$.next(users);
    });

    this.groups$ = this.usersGroupsService.getAllGroups();
  }

  getUsersOrBack() {
    let parameterIds = this.route.queryParams.pipe(
      take(1),
      tap(params => {
        if (!params['user_ids']) {
          this.router.navigate(['..'], { relativeTo: this.route });
          return observableThrowError('No user ids..');
        }
      }),
      map(params => params['user_ids'].split(',') as string[]),
      map(ids => ids.map(id => +id.trim()))
    );

    let allUsers = this.usersService.getAllUsers().pipe(take(1));

    return combineLatest(parameterIds, allUsers)
      .pipe(switchMap(([ids, users]: [number[], User[]]) => {
        let filteredUsers = users.filter(u => ids.indexOf(u.id) !== -1);
        if (filteredUsers.length !== ids.length) {
          this.router.navigate(['..'], { relativeTo: this.route });
          return observableThrowError('unknown ids...');
        }

        return of(filteredUsers);
      }));
  }

  groupsToValue(groups: UserGroup[]) {
    if (!groups) {
      return [];
    }
    return groups.map(group => group.id.toString());
  }

  submit() {
    const users = this.users$.value;
    const groupsToAdd = this.userGroupsSelectorComponent.displayedGroups;

    if (!users) {
      return;
    }

    if (groupsToAdd !== undefined && groupsToAdd.length !== 0 && !groupsToAdd.includes(undefined)) {
      this.usersService.bulkAddGroups(users, groupsToAdd)
        .pipe(take(1))
        .subscribe(() => this.router.navigate(['/management']));
    }
  }
}
