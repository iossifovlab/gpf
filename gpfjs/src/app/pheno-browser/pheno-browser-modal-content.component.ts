import { Component, Input } from '@angular/core';

import { NgbActiveModal } from '@ng-bootstrap/ng-bootstrap';

@Component({
  selector: 'pheno-browser-modal-content',
  template: `
    <div class="modal-header">
      <div class="modal-title"></div>
      <button type="button" class="close" aria-label="Close" (click)="activeModal.dismiss('Cross click')">
        <span aria-hidden="true">&times;</span>
      </button>
    </div>
    <div class="modal-body">
      <img class="pheno-browser-fullscreen-image" src="{{ imageUrl }}" />
    </div>
  `,
  styles: [`
    .modal-header {
      border-bottom: none;
    }
  `]
})
export class PhenoBrowserModalContent {
  @Input() imageUrl;

  constructor(public activeModal: NgbActiveModal) {}
}
