import { Component, OnInit } from '@angular/core';
import { UsersService } from '../users/users.service';
import { NgbActiveModal } from '@ng-bootstrap/ng-bootstrap';


@Component({
  selector: 'gpf-forgot-password',
  templateUrl: './forgot-password.component.html',
  styleUrls: ['./forgot-password.component.css']
})
export class ForgotPasswordComponent implements OnInit {
  email: string;
  resetPasswordError = '';
  resetPasswordSuccess = false;

  constructor(
    readonly activeModal: NgbActiveModal,
    private usersService: UsersService
  ) { }

  ngOnInit() {
    this.usersService.emailLog.subscribe(email => {
      this.email = email;
    });
  }

  resetPassword() {
    this.usersService.resetPassword(this.email)
    .subscribe(
      (res) => {
        if (res) {
          this.email = null;
          this.resetPasswordError = '';

          this.resetPasswordSuccess = true;
        }
      },
      (error: any) => {
        this.resetPasswordSuccess = false;
        if (error) {
          this.resetPasswordError = error;
        } else {
          this.resetPasswordError = 'Reset Password Failed';
        }
      }
    );
  }
}
