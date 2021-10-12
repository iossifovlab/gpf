import { Component, OnInit, NgZone, Input, ViewChild, ElementRef } from '@angular/core';
import { take } from 'rxjs/operators';
import { User } from '../users/users';
import { UsersService } from '../users/users.service';

@Component({
  selector: 'gpf-users-actions',
  templateUrl: './users-actions.component.html',
  styleUrls: ['./users-actions.component.css']
})
export class UsersActionsComponent implements OnInit {
  @Input() public user: User;
  @ViewChild('ele') public ele: ElementRef;
  public showDeleteButton = true;

  constructor(
    private zone: NgZone,
    private usersService: UsersService,
  ) { }

  public ngOnInit() {
    this.usersService.getUserInfo().pipe(take(1)).subscribe((currentUser) => {
      if (currentUser.email === this.user.email) {
        this.showDeleteButton = false;
      }
    });
  }

  public deleteUser(user: User): void {
    this.usersService.deleteUser(user).pipe(take(1)).subscribe(() => {
      this.reloadPage();
    });
  }

  public resetPassword(user: User): void {
    this.usersService.resetUserPassword(user).pipe(take(1)).subscribe(() => {
      this.reloadPage();
    });
  }

  private reloadPage(): void {
    this.zone.runOutsideAngular(() => {
      window.location.reload();
    });
  }

  private getUserString(user: User): string {
    let user_string = `${user.name || user.email}`
    if (user.name) {
      user_string = `(${user.email}) ` + user_string
    }
    return user_string;
  }

  public resetPasswordPopoverMessage(user: User): string {
    return `${this.getUserString(user)}'s password will be reset. An email with reset instructions will be sent and they won't be able to login until they set a new password.`
  }

  public deleteUserPopoverMessage(user: User): string {
    return `${this.getUserString(user)} will be deleted. This action is irrevertible!`
  }
}
