import { Component, OnInit } from '@angular/core';
import { UsersService } from '../users/users.service';
import { NgbActiveModal } from '@ng-bootstrap/ng-bootstrap';

@Component({
  selector: 'gpf-registration',
  templateUrl: './registration.component.html',
  styleUrls: ['./registration.component.css']
})
export class RegistrationComponent implements OnInit {
  username: string;
  firstName: string;
  lastName: string;
  researcherId: string;

  registerError = "";

  constructor(
    private activeModal: NgbActiveModal,
    private usersService: UsersService
  ) { }

  ngOnInit() {
  }

  register() {
    this.usersService.register(
      this.username, this.firstName, this.lastName, this.researcherId
    ).subscribe(
      (res) => {
        if (res) {
          this.username = null;
          this.firstName = null;
          this.lastName = null;
          this.researcherId = null;
          this.registerError = "";

          this.activeModal.close('Close click');
        }
        else {
          this.registerError = "Registration Failed";
        }

    });
  }

}
