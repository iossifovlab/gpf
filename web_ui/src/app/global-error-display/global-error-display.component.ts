import { Component, inject } from '@angular/core';
import { NgbActiveModal } from '@ng-bootstrap/ng-bootstrap';

@Component({
  selector: 'gpf-global-error-display.component',
  templateUrl: './global-error-display.component.html',
  styleUrls: ['./global-error-display.component.css'],
  standalone: false
})
export class GlobalErrorDisplayComponent {
  private activeModal = inject(NgbActiveModal);


  public closeModal(): void {
    this.activeModal.close();
  }
}
