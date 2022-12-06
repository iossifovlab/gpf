import { Component, OnInit, NgZone, Input } from '@angular/core';
import { User } from '../users/users';
import { UsersService } from '../users/users.service';
import { take } from 'rxjs/operators';

@Component({
  selector: 'gpf-users-table',
  templateUrl: './users-table.component.html',
  styleUrls: ['./users-table.component.css']
})
export class UsersTableComponent implements OnInit {
  @Input() public users: User[];
  public currentUserEmail: string;

  public constructor(
    private zone: NgZone,
    private usersService: UsersService,
  ) { }

  public ngOnInit(): void {
    this.usersService.getUserInfo().pipe(take(1)).subscribe((currentUser) => {
      this.currentUserEmail = currentUser.email;
    });
  }

  public isDefaultGroup(user: User, group: string): boolean {
    return user.getDefaultGroups().indexOf(group) !== -1;
  }

  public removeGroup(user: User, group: string): void {
    this.usersService.removeUserGroup(user, group).pipe(take(1))
      .subscribe(() => {
        this.zone.runOutsideAngular(() => {
          window.location.reload();
        });
      });
  }

  public getUserAllowedDatasetIds(user: User): string[] {
    return user.allowedDatasets.map(dataset => dataset['datasetId']);
  }
}
