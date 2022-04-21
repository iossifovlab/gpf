import { Component, OnInit, OnDestroy } from '@angular/core';
import { Router } from '@angular/router';
import { Subscription } from 'rxjs';

import { UsersService } from '../users/users.service';

@Component({
  selector: 'gpf-management',
  templateUrl: './management.component.html',
  styleUrls: ['./management.component.css']
})
export class ManagementComponent implements OnInit, OnDestroy {
  private subscription: Subscription;

  public constructor(
    private router: Router,
    private usersService: UsersService
  ) { }

  public ngOnInit(): void {
    this.subscription = this.usersService.getUserInfoObservable()
      .subscribe(userInfo => this.checkUserInfo(userInfo));
  }

  public ngOnDestroy(): void {
    if (this.subscription) {
      this.subscription.unsubscribe();
    }
  }

  public checkUserInfo(value): void {
    if (!value || !value.isAdministrator) {
      this.router.navigate(['/']);
    }
  }
}
