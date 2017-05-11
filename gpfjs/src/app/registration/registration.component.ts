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
  researcherId: string;

  registerError = "";

  constructor(
    readonly activeModal: NgbActiveModal,
    private usersService: UsersService
  ) { }

  ngOnInit() {
  }

  register() {
    this.usersService.register(
      this.email, this.name, this.researcherId
    ).subscribe(
      (res) => {
        if (res) {
          this.email = null;
          this.name = null;
          this.researcherId = null;
          this.registerError = "";

          this.activeModal.close('Close click');
        }
      },
      (error: any) => {
        if (error) {
          this.registerError = error;
        }
        else {
          this.registerError = "Registration Failed";
        }
      }
    );
  }

}
