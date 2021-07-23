import { Component, ElementRef, HostListener, OnInit, ViewChild } from '@angular/core';
import { Router } from '@angular/router';

import {throwError as observableThrowError, Observable , ReplaySubject, BehaviorSubject } from 'rxjs';

import { User } from '../users/users';
import { UsersService } from '../users/users.service';
import { UsersGroupsService } from '../users-groups/users-groups.service';
import { UserGroup } from '../users-groups/users-groups';
import { UserGroupsSelectorComponent } from 'app/user-groups-selector/user-groups-selector.component';
import { take } from 'rxjs/operators';

@Component({
  selector: 'gpf-users-create',
  templateUrl: '../user-edit/user-edit.component.html',
  styleUrls: ['../user-edit/user-edit.component.css']
})
export class UserCreateComponent implements OnInit {
  @HostListener('window:popstate', [ '$event' ])
  unloadHandler() {
    this.closeConfirmnationModal();
  }

  @ViewChild(UserGroupsSelectorComponent)
  private userGroupsSelectorComponent: UserGroupsSelectorComponent;
  @ViewChild('ele') ele: ElementRef;

  lockedOptions = {
    width: 'style',
    theme: 'bootstrap',
    multiple: true,
    tags: true,
    disabled: true,
  };

  user$ = new BehaviorSubject<User>(new User(0, '', '', [], false, []));
  groups$ = new BehaviorSubject<UserGroup[]>(null);
  createUserError = '';
  edit = false;

  constructor(
    private router: Router,
    private usersService: UsersService,
    private usersGroupsService: UsersGroupsService
  ) { }

  ngOnInit() {
    this.usersGroupsService
      .getAllGroups()
      .pipe(take(1))
      .subscribe(groups => this.groups$.next(groups));
  }

  closeConfirmnationModal() {
    this.ele.nativeElement.click();
  }

  getDefaultGroups() {
    return this.user$.value.getDefaultGroups();
  }

  submit(user: User) {
    const groupsToAdd = this.userGroupsSelectorComponent.displayedGroups;

    if (!(groupsToAdd.includes(undefined) || groupsToAdd.length === 0 || this.getDefaultGroups().includes(''))) {
      this.user$.value.groups = this.getDefaultGroups().concat(groupsToAdd);
    }

    this.usersService.createUser(user)
      .subscribe(() => this.router.navigate(['/management']),
        (error: any) => {
          if (error) {
            this.createUserError = error;
          } else {
            this.createUserError = 'Creating user failed';
          }
        }
      );
  }

  goBack() {
    this.router.navigate(['/management']);
  }
}
