import { Component, OnInit } from '@angular/core';
import { UsersService } from '../users/users.service';
import { NgbActiveModal } from '@ng-bootstrap/ng-bootstrap';

@Component({
  selector: 'gpf-forgot-password',
  templateUrl: './forgot-password.component.html',
  styleUrls: ['./forgot-password.component.css']
})
export class ForgotPasswordComponent implements OnInit {
  public email: string;
  public resetPasswordError = '';
  public resetPasswordSuccess = false;

  public constructor(
    public readonly activeModal: NgbActiveModal,
    private usersService: UsersService
  ) { }

  public ngOnInit(): void {
    this.usersService.emailLog.subscribe(email => {
      this.email = email;
    });
  }

  public resetPassword(): void {
    this.usersService.resetPassword(this.email.trim())
      .subscribe(
        (res) => {
          if (res) {
            this.email = null;
            this.resetPasswordError = '';

            this.resetPasswordSuccess = true;
          }
        },
        (error: string) => {
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
