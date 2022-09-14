import { Component, OnInit, NgZone, Input, ChangeDetectionStrategy } from '@angular/core';
import { User } from '../users/users';
import { UsersService } from '../users/users.service';
import { take } from 'rxjs/operators';
import { UserGroup } from 'app/users-groups/users-groups';
import { ItemAddEvent } from 'app/item-add-menu/item-add-menu';

@Component({
  selector: 'gpf-users-table',
  templateUrl: './users-table.component.html',
  styleUrls: ['./users-table.component.css'],
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class UsersTableComponent implements OnInit {
  @Input() public users: User[];
  @Input() public allGroups: UserGroup[];
  public allGroupNames: string[] = [];
  public currentUserEmail: string;

  // Primitive used for triggering change detection
  public manualPipeTrigger = 0;

  public constructor(
    private zone: NgZone,
    private usersService: UsersService,
  ) { }

  public ngOnInit(): void {
    this.usersService.getUserInfo().pipe(take(1)).subscribe((currentUser: User) => {
      this.currentUserEmail = currentUser.email;
    });

    this.allGroupNames = this.allGroups.map(group => group.name);
  }

  public isDefaultGroup(user: User, group: string): boolean {
    return user.getDefaultGroups().indexOf(group) !== -1;
  }

  public removeGroup(user: User, group: string): void {
    this.usersService.removeUserGroup(user, group);

    this.manualPipeTrigger++;
  }

  public addGroup(user: User, event$: ItemAddEvent): void {
    user.groups.push(event$.item);

    const userClone = user.clone();
    // Taken from user-edit component. Why delete the email? Precaution?
    delete userClone.email;
    this.usersService.updateUser(userClone);
  }

  public getUserAllowedDatasetIds(user: User): string[] {
    return user.allowedDatasets.map(dataset => dataset['datasetId']);
  }
}
