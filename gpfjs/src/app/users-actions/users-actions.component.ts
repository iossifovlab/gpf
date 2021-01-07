import { Component, OnInit, NgZone, Input, ViewChild, ElementRef, OnDestroy } from '@angular/core';

import { User } from '../users/users';
import { UsersService } from '../users/users.service';

@Component({
  selector: 'gpf-users-actions',
  templateUrl: './users-actions.component.html',
  styleUrls: ['./users-actions.component.css']
})
export class UsersActionsComponent implements OnInit, OnDestroy {
  @Input()
  user: User;
  @ViewChild('ele') ele: ElementRef;

  constructor(
    private zone: NgZone,
    private usersService: UsersService,
  ) { }

  ngOnInit() {
  }

  ngOnDestroy(): void {
    this.closeConfirmnationModal();
  }

  closeConfirmnationModal() {
    this.ele.nativeElement.click();
  }

  deleteUser(user: User) {
    this.usersService.deleteUser(user).take(1)
      .subscribe(() => {
        this.reloadPage();
      });
  }

  resetPassword(user: User) {
    this.usersService.resetUserPassword(user).take(1)
      .subscribe(() => {
        this.reloadPage();
      });
  }

  reloadPage() {
    this.zone.runOutsideAngular(() => {
      window.location.reload();
    });
  }

  getUserString(user: User) {
    let user_string = `${user.name || user.email}`
    if(user.name) {
      user_string = `(${user.email}) ` + user_string
    }
    return user_string;
  }

  resetPasswordPopoverMessage(user: User) {
    return `${this.getUserString(user)}'s password will be reset. An email with reset instructions will be sent and they won't be able to login until they set a new password.`
  }

  deleteUserPopoverMessage(user: User) {
    return `${this.getUserString(user)} will be deleted. This action is irrevertible!`
  }

}
