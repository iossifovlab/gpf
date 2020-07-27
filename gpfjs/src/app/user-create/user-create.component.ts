import { Component, OnInit, ViewChild } from '@angular/core';
import { Router } from '@angular/router';

import { BehaviorSubject } from 'rxjs';

import { User } from '../users/users';
import { UsersService } from '../users/users.service';
import { UsersGroupsService } from '../users-groups/users-groups.service';
import { UserGroup } from '../users-groups/users-groups';
import { UserGroupsSelectorComponent } from 'app/user-groups-selector/user-groups-selector.component';

@Component({
  selector: 'gpf-users-create',
  templateUrl: '../user-edit/user-edit.component.html',
  styleUrls: ['../user-edit/user-edit.component.css']
})
export class UserCreateComponent implements OnInit {
  @ViewChild(UserGroupsSelectorComponent)
  private userGroupsSelectorComponent: UserGroupsSelectorComponent;

  lockedOptions = {
    width: 'style',
    theme: 'bootstrap',
    multiple: true,
    tags: true,
    disabled: true,
  };
  user$ = new BehaviorSubject<User>(new User(0, '', '', [], false));
  groups$ = new BehaviorSubject<UserGroup[]>(null);

  edit = false;

  constructor(
    private router: Router,
    private usersService: UsersService,
    private usersGroupsService: UsersGroupsService
  ) { }

  ngOnInit() {
    this.usersGroupsService
      .getAllGroups()
      .take(1)
      .subscribe(groups => this.groups$.next(groups));
  }

  getDefaultGroups() {
    return this.user$.value.getDefaultGroups();
  }

  submit(user: User) {
    const selectedGroups = this.userGroupsSelectorComponent.selectedGroups;

    if (!selectedGroups.includes(undefined)) {
      this.user$.value.groups = this.getDefaultGroups().concat(selectedGroups);
    }

    this.usersService.createUser(user)
      .take(1)
      .subscribe(() => this.router.navigate(['/management']));
  }

  goBack() {
    this.router.navigate(['/management']);
  }
}
