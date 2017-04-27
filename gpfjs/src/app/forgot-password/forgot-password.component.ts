import { Component, OnInit, Output, EventEmitter } from '@angular/core';
import { NgbActiveModal } from '@ng-bootstrap/ng-bootstrap';

@Component({
  selector: 'gpf-forgot-password',
  templateUrl: './forgot-password.component.html',
  styleUrls: ['./forgot-password.component.css']
})
export class ForgotPasswordComponent implements OnInit {
  @Output() onClose = new EventEmitter();

  constructor(
    private activeModal: NgbActiveModal
  ) { }

  ngOnInit() {
  }

}
