import { Component, Input } from '@angular/core';
import { NgbActiveModal } from '@ng-bootstrap/ng-bootstrap';

@Component({
  selector: 'gpf-popup',
  templateUrl: './popup.component.html',
  styleUrls: ['./popup.component.css']
})
export class PopupComponent {

  @Input() data;

  constructor(
    public activeModal: NgbActiveModal) {}

  closeModal() {
    this.activeModal.close();
  }
}
