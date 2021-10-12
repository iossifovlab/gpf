import { Component, OnInit } from '@angular/core';
import { UsersService } from '../users/users.service';
import { NgbActiveModal } from '@ng-bootstrap/ng-bootstrap';

@Component({
  selector: 'gpf-registration',
  templateUrl: './registration.component.html',
  styleUrls: ['./registration.component.css']
})
export class RegistrationComponent implements OnInit {
  email: string;
  name: string;

  registerError = '';
  registerSuccess = false;

  constructor(
    readonly activeModal: NgbActiveModal,
    private usersService: UsersService
  ) { }

  ngOnInit() {
    this.usersService.emailLog.subscribe(email => {
      this.email = email;
    });
  }

  register() {
    this.usersService.register(
      this.email, this.name
    ).subscribe(
      (res) => {
        if (res) {
          this.email = null;
          this.name = null;
          this.registerError = '';

          this.registerSuccess = true;
        }
      },
      (error: any) => {
        this.registerSuccess = false;
        if (error) {
          this.registerError = error;
        } else {
          this.registerError = 'Registration Failed';
        }
      }
    );
  }

}
