import { Component, OnInit, OnDestroy } from '@angular/core';
import { Router } from '@angular/router';

import { UsersService } from '../users/users.service';

@Component({
  selector: 'gpf-management',
  templateUrl: './management.component.html',
  styleUrls: ['./management.component.css']
})
export class ManagementComponent implements OnInit, OnDestroy {
  private subscription;

  constructor(
    private router: Router,
    private usersService: UsersService
  ) { }

  ngOnInit() {
    this.subscription = this.usersService.getUserInfoObservable()
      .subscribe(userInfo => this.checkUserInfo(userInfo));
  }

  ngOnDestroy() {
    if (this.subscription) {
      this.subscription.unsubscribe();
    }
  }

  checkUserInfo(value) {
    if (!value || !value.isAdministrator) {
      this.router.navigate(['/']);
    }
  }

}
