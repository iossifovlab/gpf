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
  resetPasswordError = "";

  constructor(
    readonly activeModal: NgbActiveModal,
    private usersService: UsersService
  ) { }

  ngOnInit() {
  }

  resetPassword() {
    this.usersService.resetPassword(this.email)
    .subscribe(
      (res) => {
        if (res) {
          this.email = null;
          this.resetPasswordError = "";

          this.activeModal.close('Close click');
        }
      },
      (error: any) => {
        if (error) {
          this.resetPasswordError = error;
        }
        else {
          this.resetPasswordError = "Reset Password Failed";
        }
      }
    )
  }
}
