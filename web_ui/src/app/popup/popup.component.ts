import { Component, Input, inject } from '@angular/core';
import { NgbActiveModal } from '@ng-bootstrap/ng-bootstrap';

@Component({
  selector: 'gpf-popup',
  templateUrl: './popup.component.html',
  styleUrls: ['./popup.component.css'],
  standalone: false
})
export class PopupComponent {
  activeModal = inject(NgbActiveModal);

  @Input() public data;

  public closeModal(): void {
    this.activeModal.close();
  }
}
