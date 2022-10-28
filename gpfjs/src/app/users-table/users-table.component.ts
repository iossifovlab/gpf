import { Component, OnInit, NgZone, Input, ChangeDetectionStrategy } from '@angular/core';
import { User } from '../users/users';
import { UsersService } from '../users/users.service';
import { take } from 'rxjs/operators';
import { ItemAddEvent } from 'app/item-add-menu/item-add-menu';
import { UsersGroupsService } from 'app/users-groups/users-groups.service';

@Component({
  selector: 'gpf-users-table',
  templateUrl: './users-table.component.html',
  styleUrls: ['./users-table.component.css'],
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class UsersTableComponent implements OnInit {
  @Input() public users: User[];
  public currentUserEmail: string;

  public allGroupNames: string[] = [];
  public shownGroupNames: string[] = [];
  private addItemMenuPagesCounter = 0;
  private loadingAddItemMenuPage = false;

  public constructor(
    private zone: NgZone,
    private usersService: UsersService,
    private usersGroupsService: UsersGroupsService
  ) { }

  public ngOnInit(): void {
    this.usersService.getUserInfo().pipe(take(1)).subscribe((currentUser: User) => {
      this.currentUserEmail = currentUser.email;
    });

    this.updateAddItemMenuItems();
  }

  public isDefaultGroup(user: User, group: string): boolean {
    return user.getDefaultGroups().indexOf(group) !== -1;
  }

  public removeGroup(user: User, group: string): void {
    this.usersService.removeUserGroup(user, group).pipe(take(1)).subscribe((res: User) => {
      user.groups = res.groups;
      user.allowedDatasets = res.allowedDatasets;
    });
  }

  public addGroup(user: User, event$: ItemAddEvent): void {
    const userClone = user.clone();
    userClone.groups.push(event$.item);

    this.usersService.updateUser(userClone).pipe(take(1)).subscribe((res: User) => {
      user.groups = res.groups;
      user.allowedDatasets = res.allowedDatasets;
    });
  }

  public getUserAllowedDatasetIds(user: User): string[] {
    return user.allowedDatasets.map(dataset => dataset['datasetId']);
  }

  public updateAddItemMenuItems(): void {
    if (!this.loadingAddItemMenuPage) {
      this.addItemMenuPagesCounter++;
      this.loadingAddItemMenuPage = true;
      // implement group search in menu
      this.usersGroupsService.getGroups(this.addItemMenuPagesCounter, '').subscribe(res => {
        this.allGroupNames = this.allGroupNames.concat(res.map(group => group.name));
        this.loadingAddItemMenuPage = false;
      });
    }
  }

  public filterShownGroupNames(userGroups: string[]): void {
    this.shownGroupNames = this.allGroupNames.filter(element => userGroups.indexOf(element) === -1);
  }
}
