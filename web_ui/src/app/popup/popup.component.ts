import { Component, Input } from '@angular/core';
import { NgbActiveModal } from '@ng-bootstrap/ng-bootstrap';

@Component({
  selector: 'gpf-popup',
  templateUrl: './popup.component.html',
  styleUrls: ['./popup.component.css'],
  standalone: false
})
export class PopupComponent {
  @Input() public data;

  public constructor(
    public activeModal: NgbActiveModal
  ) {}

  public closeModal(): void {
    this.activeModal.close();
  }
}
