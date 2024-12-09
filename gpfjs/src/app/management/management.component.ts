import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';

import { UsersService } from '../users/users.service';
import { UserInfo } from 'app/users/users';

@Component({
  selector: 'gpf-management',
  templateUrl: './management.component.html',
  styleUrls: ['./management.component.css']
})
export class ManagementComponent implements OnInit {
  public showTemplate = false;

  public constructor(
    private router: Router,
    private usersService: UsersService
  ) { }

  public ngOnInit(): void {
    const user: UserInfo = this.usersService.cachedUserInfo();
    this.checkUserInfo(user);
  }

  private checkUserInfo(user: UserInfo): void {
    if (user?.isAdministrator) {
      this.showTemplate = true;
    } else {
      this.router.navigate(['/']);
    }
  }
}
