import { Component, ElementRef, HostListener, OnInit, ViewChild } from '@angular/core';
import { Router, ActivatedRoute } from '@angular/router';

// tslint:disable-next-line:import-blacklist
import { BehaviorSubject } from 'rxjs';

import { User } from '../users/users';
import { UsersService } from '../users/users.service';
import { UserGroup } from '../users-groups/users-groups';
import { UsersGroupsService } from '../users-groups/users-groups.service';
import { IDropdownSettings } from 'ng-multiselect-dropdown';
import { UserGroupsSelectorComponent } from 'app/user-groups-selector/user-groups-selector.component';
import { map, switchMap, take } from 'rxjs/operators';

@Component({
  selector: 'gpf-user-edit',
  templateUrl: './user-edit.component.html',
  styleUrls: ['./user-edit.component.css']
})
export class UserEditComponent implements OnInit {
  @ViewChild(UserGroupsSelectorComponent)
  private userGroupsSelectorComponent: UserGroupsSelectorComponent;
  @ViewChild('ele') ele: ElementRef;
  @ViewChild('nameInput') nameInput: ElementRef;

  dropdownSettings: IDropdownSettings = {};

  lockedOptions = {
    width: 'style',
    theme: 'bootstrap',
    multiple: true,
    tags: true,
    disabled: true,
  };

  user$ = new BehaviorSubject<User>(null);
  groups$ = new BehaviorSubject<UserGroup[]>(null);
  emailValue: string;

  edit = true;

  constructor(
    private router: Router,
    private route: ActivatedRoute,
    private usersService: UsersService,
    private usersGroupsService: UsersGroupsService
  ) { }

  @HostListener('window:popstate', [ '$event' ])
  unloadHandler() {
    this.closeConfirmnationModal();
  }

  ngOnInit() {
    this.focusNameInputArea();

    this.route.params.pipe(
      take(1),
      map(params => +params['id']),
      switchMap(userId => this.usersService.getUser(userId))
    ).subscribe(user => {
      this.emailValue = user.email;
      this.user$.next(user);
    });

    this.usersGroupsService
    .getAllGroups()
    .subscribe(groups => this.groups$.next(groups));

    this.dropdownSettings = {
      singleSelection: true,
      idField: 'id',
      textField: 'text',
      allowSearchFilter: true,
    };
  }

  closeConfirmnationModal() {
    this.ele.nativeElement.click();
  }

  getDefaultGroups() {
    return ['any_user', this.emailValue];
  }

  submit(user) {
    const groupsToAdd = this.userGroupsSelectorComponent.displayedGroups;

    if (!groupsToAdd.includes(undefined)) {
      this.user$.value.groups = this.getDefaultGroups().concat(groupsToAdd);
    }

    delete user.email;
    this.usersService.updateUser(user)
      .pipe(take(1))
      .subscribe(() => this.router.navigate(['/management']));
  }

  goBack() {
    this.router.navigate(['/management']);
  }

  /**
  * Waits name input area element to load.
  * @returns promise
  */
   private async waitForNameInputAreaToLoad(): Promise<void> {
    return new Promise<void>(resolve => {
      const timer = setInterval(() => {
        if (this.nameInput !== undefined) {
          resolve();
          clearInterval(timer);
        }
      }, 100);
    });
  }

  private focusNameInputArea() {
    this.waitForNameInputAreaToLoad().then(() => {
      this.nameInput.nativeElement.focus();
    });
  }
}
