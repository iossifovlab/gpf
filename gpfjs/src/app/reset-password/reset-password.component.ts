import { Component, ViewChild, AfterViewInit } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { ConfigService } from 'app/config/config.service';
import { UsersService } from '../users/users.service';

@Component({
  selector: 'gpf-reset-password',
  templateUrl: './reset-password.component.html',
  styleUrls: ['./reset-password.component.css']
})
export class ResetPasswordComponent implements AfterViewInit {
  @ViewChild('content') content;
  password: string;
  confirmPassword: string;
  verifPath: string;

  resetPasswordError = '';
  verifPathValid = false;

  constructor(
    private router: Router,
    private usersService: UsersService,
    private route: ActivatedRoute,
    private config: ConfigService,
  ) { }

  ngAfterViewInit() {
    this.verifPath = this.route.snapshot.params['validateString'];
    this.usersService.checkVerification(this.verifPath).subscribe(
      (res) => {
        if (res) {
          this.verifPathValid = true;
        } else {
          this.verifPathValid = false;
          this.resetPasswordError = 'Invalid verification URL';
        }
    });
  }

  resetPassword() {
    if (this.password !== this.confirmPassword) {
      this.resetPasswordError = 'Passwords don\'t match';
      return;
    }

    if (this.password.length < 10) {
      this.resetPasswordError = 'Password must be at least 10 symbols long';
      return;
    }

    this.usersService.changePassword(this.password, this.verifPath).subscribe(
      (res) => {
        if (res) {
          this.password = null;
          this.confirmPassword = null;
          this.resetPasswordError = '';
          this.router.navigateByUrl(this.config.baseUrl);
        } else {
          this.resetPasswordError = 'Reset Password Failed';
        }
    });
  }
}
