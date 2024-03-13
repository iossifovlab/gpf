import { ChangeDetectionStrategy, Component, ElementRef, HostListener, OnInit, ViewChild } from '@angular/core';
import { Router, ActivatedRoute } from '@angular/router';
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
  styleUrls: ['./user-edit.component.css'],
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class UserEditComponent implements OnInit {
  @ViewChild(UserGroupsSelectorComponent)
  private userGroupsSelectorComponent: UserGroupsSelectorComponent;
  @ViewChild('ele') public ele: ElementRef;
  @ViewChild('nameInput') public nameInput: ElementRef;

  public dropdownSettings: IDropdownSettings = {};
  public createUserError = '';
  public user$ = new BehaviorSubject<User>(null);
  public groups$ = new BehaviorSubject<UserGroup[]>(null);
  private emailValue: string;

  public edit = true;

  public constructor(
    private router: Router,
    private route: ActivatedRoute,
    private usersService: UsersService,
    private usersGroupsService: UsersGroupsService
  ) { }

  @HostListener('window:popstate', ['$event'])
  public unloadHandler(): void {
    this.closeConfirmnationModal();
  }

  public ngOnInit(): void {
    this.focusNameInputArea();

    this.route.params.pipe(
      take(1),
      map(params => +params['id']),
      switchMap(userId => this.usersService.getUser(userId))
    ).subscribe(user => {
      this.emailValue = user.email;
      this.user$.next(user);
    });

    this.usersGroupsService.getAllGroups().subscribe(groups => this.groups$.next(groups));

    this.dropdownSettings = {
      singleSelection: true,
      idField: 'id',
      textField: 'text',
      allowSearchFilter: true,
    };
  }

  private closeConfirmnationModal(): void {
    this.ele.nativeElement.click();
  }

  public getDefaultGroups(): string[] {
    return ['any_user', this.emailValue];
  }

  public submit(user: User): void {
    const groupsToAdd = this.userGroupsSelectorComponent.displayedGroups;

    if (!groupsToAdd.includes(undefined)) {
      this.user$.value.groups = this.getDefaultGroups().concat(groupsToAdd);
    }

    delete user.email;
    this.usersService.updateUser(user)
      .pipe(take(1))
      .subscribe(() => this.router.navigate(['/management']));
  }

  public goBack(): void {
    this.router.navigate(['/management']);
  }

  private async waitForNameInputAreaToLoad(): Promise<void> {
    return new Promise<void>(resolve => {
      const timer = setInterval(() => {
        if (this.nameInput !== undefined) {
          resolve();
          clearInterval(timer);
        }
      }, 50);
    });
  }

  private focusNameInputArea(): void {
    this.waitForNameInputAreaToLoad().then(() => {
      (this.nameInput.nativeElement as HTMLInputElement).focus();
    });
  }
}
