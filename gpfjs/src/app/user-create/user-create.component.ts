import { Component, ElementRef, HostListener, OnInit, ViewChild } from '@angular/core';
import { Router } from '@angular/router';
import { BehaviorSubject } from 'rxjs';
import { User } from '../users/users';
import { UsersService } from '../users/users.service';
import { UsersGroupsService } from '../users-groups/users-groups.service';
import { UserGroup } from '../users-groups/users-groups';
import { UserGroupsSelectorComponent } from 'app/user-groups-selector/user-groups-selector.component';
import { take } from 'rxjs/operators';
import { IDropdownSettings } from 'ng-multiselect-dropdown';

@Component({
  selector: 'gpf-users-create',
  templateUrl: '../user-edit/user-edit.component.html',
  styleUrls: ['../user-edit/user-edit.component.css']
})
export class UserCreateComponent implements OnInit {
  @ViewChild(UserGroupsSelectorComponent)
  private userGroupsSelectorComponent: UserGroupsSelectorComponent;
  @ViewChild('ele') public ele: ElementRef;
  @ViewChild('emailInput') public emailInput: ElementRef;

  public user$ = new BehaviorSubject<User>(new User(0, '', '', [], false, []));
  public groups$ = new BehaviorSubject<UserGroup[]>(null);
  public createUserError = '';
  public edit = false;
  public dropdownSettings: IDropdownSettings = {};

  public constructor(
    private router: Router,
    private usersService: UsersService,
    private usersGroupsService: UsersGroupsService
  ) { }

  @HostListener('window:popstate', ['$event'])
  public unloadHandler(): void {
    this.closeConfirmnationModal();
  }

  public ngOnInit(): void {
    this.focusEmailInputArea();
    this.usersGroupsService
      .getAllGroups()
      .pipe(take(1))
      .subscribe(groups => this.groups$.next(groups));
  }

  private closeConfirmnationModal(): void {
    this.ele.nativeElement.click();
  }

  public getDefaultGroups(): string[] {
    return this.user$.value.getDefaultGroups();
  }

  public submit(user: User): void {
    const groupsToAdd = this.userGroupsSelectorComponent.displayedGroups;

    if (!(groupsToAdd.includes(undefined))) {
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

  public goBack(): void {
    this.router.navigate(['/management']);
  }

  private async waitForEmailInputAreaToLoad(): Promise<void> {
    return new Promise<void>(resolve => {
      const timer = setInterval(() => {
        if (this.emailInput !== undefined) {
          resolve();
          clearInterval(timer);
        }
      }, 100);
    });
  }

  private focusEmailInputArea(): void {
    this.waitForEmailInputAreaToLoad().then(() => {
      this.emailInput.nativeElement.focus();
    });
  }
}
